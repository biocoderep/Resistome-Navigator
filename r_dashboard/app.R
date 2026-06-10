# ==============================================================================
# Script: app.R
# Project: AMR VetGenomeHub
# Purpose: Interactive Shiny Dashboard for Cohort Analysis
# ==============================================================================

if (!require("pacman")) install.packages("pacman")
pacman::p_load(shiny, shinydashboard, tidyverse, plotly, visNetwork, DT, jsonlite)

# Configuration for where to find the batch data
# You can change this to your actual upload dir or pass via environment variable
UPLOAD_DIR <- Sys.getenv("UPLOAD_DIR", unset = "/tmp/amr_uploads")
if (Sys.info()["sysname"] == "Windows" && UPLOAD_DIR == "/tmp/amr_uploads") {
  UPLOAD_DIR <- "C:/tmp/amr_uploads"
}

# 1. HELPER FUNCTIONS
# ------------------------------------------------------------------------------
get_available_batches <- function() {
  if(!dir.exists(UPLOAD_DIR)) return(c("No batches found"))
  
  files <- list.files(UPLOAD_DIR, pattern = "^batch_.*_data\\.json$")
  if(length(files) == 0) return(c("No batches found"))
  
  # Extract batch IDs
  batch_ids <- gsub("^batch_(.*)_data\\.json$", "\\1", files)
  return(batch_ids)
}

load_batch_data <- function(batch_id) {
  file_path <- file.path(UPLOAD_DIR, sprintf("batch_%s_data.json", batch_id))
  if(!file.exists(file_path)) return(NULL)
  
  tryCatch({
    return(fromJSON(file_path))
  }, error = function(e) {
    return(NULL)
  })
}

# Define a nice color palette
CARBON_COLORS <- c('#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56', 
                   '#570408', '#198038', '#002d9c', '#ee5396', '#b28600',
                   '#009d9a', '#012749', '#8a3800', '#a56eff')

# 2. UI DESIGN
# ------------------------------------------------------------------------------
ui <- dashboardPage(
  skin = "red",
  dashboardHeader(title = "AMR Command Center"),
  
  dashboardSidebar(
    sidebarMenu(
      menuItem("Dashboard Overview", tabName = "overview", icon = icon("dashboard")),
      menuItem("Resistome UMAP", tabName = "umap", icon = icon("project-diagram")),
      menuItem("Co-occurrence Network", tabName = "network", icon = icon("share-alt")),
      menuItem("Resistance Barcode", tabName = "barcode", icon = icon("barcode")),
      menuItem("Data Explorer", tabName = "data", icon = icon("table"))
    ),
    
    hr(),
    # Global Filters
    selectInput("batch_filter", "Select Batch ID:", choices = get_available_batches())
  ),
  
  dashboardBody(
    uiOutput("embed_css"),
    tags$head(tags$style(HTML("
      .info-box { min-height: 100px; }
      .info-box-icon { height: 100px; line-height: 100px; }
      .box-header .box-title { font-weight: bold; }
      
      /* Optional embedded styling */
      .embedded-mode .main-header { display: none !important; }
      .embedded-mode .main-sidebar { display: none !important; }
      .embedded-mode .content-wrapper, .embedded-mode .right-side, .embedded-mode .main-footer { margin-left: 0 !important; }
    "))),
    
    tabItems(
      # TAB 1: OVERVIEW
      tabItem(tabName = "overview",
              h2("Cohort Analytics: Antimicrobial Resistance"),
              p("This dashboard provides interactive population-level insights into the resistome of your sequenced batches."),
              fluidRow(
                infoBoxOutput("total_isolates_box"),
                infoBoxOutput("total_antibiotics_box"),
                infoBoxOutput("network_nodes_box")
              )
      ),
      
      # TAB 2: UMAP
      tabItem(tabName = "umap",
              fluidRow(
                box(width = 12, title = "Live 3D UMAP", status = "danger", solidHeader = TRUE,
                    plotlyOutput("umap_chart", height = 600))
              )
      ),
      
      # TAB 3: NETWORK
      tabItem(tabName = "network",
              fluidRow(
                box(width = 12, title = "Gene Co-occurrence Network", status = "primary", solidHeader = TRUE,
                    visNetworkOutput("network_chart", height = 600))
              )
      ),
      
      # TAB 4: BARCODE
      tabItem(tabName = "barcode",
              fluidRow(
                box(width = 12, title = "Population Resistance Barcode", status = "warning", solidHeader = TRUE,
                    plotlyOutput("barcode_chart", height = 600))
              )
      ),
      
      # TAB 5: DATA TABLE
      tabItem(tabName = "data",
              fluidRow(
                box(width = 12, title = "Detailed Prediction Profiles", status = "success", solidHeader = TRUE,
                    DTOutput("data_table"))
              )
      )
    )
  )
)

# 3. SERVER LOGIC
# ------------------------------------------------------------------------------
server <- function(input, output, session) {
  
  # Read URL query parameters
  observe({
    query <- parseQueryString(session$clientData$url_search)
    
    if (!is.null(query$batch_id)) {
      updateSelectInput(session, "batch_filter", selected = query$batch_id)
    }
    
    if (!is.null(query$embed) && query$embed == "true") {
      # Add embedded-mode class to body to hide sidebar and header
      output$embed_css <- renderUI({
        tags$script("document.body.classList.add('embedded-mode');")
      })
    }
  })
  
  # Add auto-refresh for batch list
  observe({
    invalidateLater(5000, session)
    curr <- isolate(input$batch_filter)
    choices <- get_available_batches()
    if(!identical(curr, choices) && curr %in% choices) {
      updateSelectInput(session, "batch_filter", choices = choices, selected = curr)
    } else if (!identical(curr, choices)) {
      updateSelectInput(session, "batch_filter", choices = choices)
    }
  })
  
  batch_data <- reactive({
    req(input$batch_filter != "No batches found")
    load_batch_data(input$batch_filter)
  })
  
  # --- Value Boxes ---
  output$total_isolates_box <- renderInfoBox({
    data <- batch_data()
    n_iso <- if(!is.null(data$population_barcode$isolates)) length(data$population_barcode$isolates) else 0
    infoBox("Isolates in Batch", n_iso, icon = icon("vials"), color = "blue")
  })
  
  output$total_antibiotics_box <- renderInfoBox({
    data <- batch_data()
    n_ab <- if(!is.null(data$population_barcode$antibiotics)) length(data$population_barcode$antibiotics) else 0
    infoBox("Antibiotics Profiled", n_ab, icon = icon("pills"), color = "red")
  })
  
  output$network_nodes_box <- renderInfoBox({
    data <- batch_data()
    n_nodes <- if(!is.null(data$gene_cooccurrence_network$nodes)) nrow(as.data.frame(data$gene_cooccurrence_network$nodes)) else 0
    infoBox("Genes in Network", n_nodes, icon = icon("dna"), color = "yellow")
  })
  
  # --- UMAP Tab ---
  output$umap_chart <- renderPlotly({
    req(batch_data())
    data <- batch_data()
    req(!is.null(data$resistome_umap))
    
    df <- as.data.frame(data$resistome_umap)
    req(nrow(df) > 0)
    
    # 3D Plotly Scatter
    p <- plot_ly(df, x = ~x, y = ~y, z = ~z, color = ~dominant_resistance, colors = CARBON_COLORS,
                 text = ~id, hoverinfo = "text+color",
                 type = "scatter3d", mode = "markers",
                 marker = list(size = 5, opacity = 0.8)) %>%
      layout(scene = list(
        xaxis = list(title = "UMAP 1"),
        yaxis = list(title = "UMAP 2"),
        zaxis = list(title = "UMAP 3")
      ))
    p
  })
  
  # --- Network Tab ---
  output$network_chart <- renderVisNetwork({
    req(batch_data())
    data <- batch_data()
    req(!is.null(data$gene_cooccurrence_network))
    
    nodes <- as.data.frame(data$gene_cooccurrence_network$nodes)
    links <- as.data.frame(data$gene_cooccurrence_network$links)
    req(nrow(nodes) > 0, nrow(links) > 0)
    
    # Map visNetwork columns
    vis_nodes <- nodes %>%
      rename(id = id, label = name, value = val, group = group) %>%
      mutate(title = paste0("<p><b>", label, "</b><br>Class: ", group, "</p>"))
      
    vis_edges <- links %>%
      rename(from = source, to = target, value = value)
      
    visNetwork(vis_nodes, vis_edges) %>%
      visNodes(font = list(size = 16, face = "bold"), shape = "dot") %>%
      visEdges(color = list(color = "rgba(100,116,139,0.4)")) %>%
      visOptions(highlightNearest = TRUE, nodesIdSelection = TRUE) %>%
      visPhysics(stabilization = FALSE, solver = "forceAtlas2Based",
                 forceAtlas2Based = list(gravitationalConstant = -50)) %>%
      visLegend()
  })
  
  # --- Barcode Tab ---
  output$barcode_chart <- renderPlotly({
    req(batch_data())
    data <- batch_data()
    req(!is.null(data$population_barcode))
    
    isolates <- data$population_barcode$isolates
    req(length(isolates) > 0)
    
    # Flatten
    df_list <- lapply(isolates, function(iso) {
      prof <- iso$profile
      prof$isolate <- iso$filename
      as.data.frame(prof, stringsAsFactors = FALSE)
    })
    barcode_df <- bind_rows(df_list)
    
    long_df <- barcode_df %>%
      pivot_longer(cols = -isolate, names_to = "Antibiotic", values_to = "Prediction")
    
    # Sort
    long_df$isolate <- factor(long_df$isolate, levels = rev(sort(unique(long_df$isolate))))
    
    p <- ggplot(long_df, aes(x = Antibiotic, y = isolate, fill = Prediction)) +
      geom_tile(color = "white") +
      scale_fill_manual(values = c("S" = "#198038", "I" = "#b28600", "R" = "#da1e28", "N/A" = "gray")) +
      theme_minimal() +
      labs(x = "Antibiotic", y = "Isolate") +
      theme(axis.text.x = element_text(angle = 45, hjust = 1))
      
    ggplotly(p, tooltip = c("x", "y", "fill"))
  })
  
  # --- Data Tab ---
  output$data_table <- renderDT({
    req(batch_data())
    data <- batch_data()
    req(!is.null(data$population_barcode))
    
    isolates <- data$population_barcode$isolates
    req(length(isolates) > 0)
    
    df_list <- lapply(isolates, function(iso) {
      prof <- iso$profile
      prof$isolate <- iso$filename
      as.data.frame(prof, stringsAsFactors = FALSE)
    })
    barcode_df <- bind_rows(df_list) %>% select(isolate, everything())
    
    datatable(barcode_df, options = list(pageLength = 20, scrollX = TRUE), 
              class = "display nowrap compact", filter = 'top')
  })
}

shinyApp(ui, server)
