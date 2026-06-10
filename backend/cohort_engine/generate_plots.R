# generate_plots.R
# Arguments: 
# 1. JSON data file path
# 2. Output directory

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  stop("Usage: Rscript generate_plots.R <data.json> <output_dir>")
}

data_file <- args[1]
output_dir <- args[2]

suppressPackageStartupMessages({
  library(jsonlite)
  library(ggplot2)
  library(dplyr)
  library(tidyr)
  library(igraph)
  library(ggraph)
})

# Ensure output directory exists
if (!dir.exists(output_dir)) {
  dir.create(output_dir, recursive = TRUE)
}

# Read JSON data
data <- fromJSON(data_file)

# Theme for publication
pub_theme <- theme_minimal(base_size = 14) +
  theme(
    plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
    plot.subtitle = element_text(size = 12, hjust = 0.5, color = "gray40"),
    panel.grid.minor = element_blank(),
    legend.position = "bottom"
  )

carbon_colors <- c('#6929c4', '#1192e8', '#005d5d', '#9f1853', '#fa4d56', '#570408', '#198038', '#002d9c', '#ee5396', '#b28600')

# ==========================================
# 1. UMAP Plot
# ==========================================
if (!is.null(data$resistome_umap)) {
  umap_df <- as.data.frame(data$resistome_umap)
  
  p_umap <- ggplot(umap_df, aes(x = x, y = y, color = dominant_resistance)) +
    geom_point(size = 3, alpha = 0.8) +
    scale_color_manual(values = carbon_colors) +
    labs(title = "Resistome UMAP", x = "UMAP 1", y = "UMAP 2", color = "Dominant Class") +
    pub_theme
  
  ggsave(file.path(output_dir, "umap.png"), p_umap, width = 8, height = 6, dpi = 300)
}

# ==========================================
# 2. Gene Co-occurrence Network
# ==========================================
if (!is.null(data$gene_cooccurrence_network)) {
  net_data <- data$gene_cooccurrence_network
  nodes <- as.data.frame(net_data$nodes)
  links <- as.data.frame(net_data$links)
  
  if (nrow(links) > 0) {
    g <- graph_from_data_frame(d = links, vertices = nodes, directed = FALSE)
    
    p_net <- ggraph(g, layout = 'fr') + 
      geom_edge_link(aes(width = value), alpha = 0.3, color = "gray50") + 
      geom_node_point(aes(size = val, color = group), alpha = 0.9) +
      geom_node_text(aes(label = name), repel = TRUE, size = 4, fontface = "bold") +
      scale_size_continuous(range = c(3, 10), guide = "none") +
      scale_edge_width(range = c(0.5, 2), guide = "none") +
      scale_color_manual(values = carbon_colors) +
      labs(title = "AMR Gene Co-occurrence Network", color = "Class") +
      theme_void(base_size = 14) +
      theme(
        plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
        legend.position = "bottom"
      )
    
    ggsave(file.path(output_dir, "network.png"), p_net, width = 8, height = 8, dpi = 300)
  }
}

# ==========================================
# 3. Population Resistance Barcode
# ==========================================
if (!is.null(data$population_barcode)) {
  barcode <- data$population_barcode
  isolates <- barcode$isolates
  
  # Flatten list of lists to data frame
  # isolates looks like: [{sample_id: "x", filename: "y", profile: {AMP: "R", GEN: "S"}}, ...]
  
  df_list <- lapply(isolates, function(iso) {
    prof <- iso$profile
    prof$isolate <- iso$filename
    as.data.frame(prof, stringsAsFactors = FALSE)
  })
  barcode_df <- bind_rows(df_list)
  
  # Melt to long format
  barcode_long <- barcode_df %>%
    pivot_longer(cols = -isolate, names_to = "Antibiotic", values_to = "Prediction")
  
  # Order isolates alphabetically (or could cluster them)
  barcode_long$isolate <- factor(barcode_long$isolate, levels = sort(unique(barcode_long$isolate), decreasing=TRUE))
  
  # Colors
  sir_cols <- c("S" = "#198038", "I" = "#b28600", "R" = "#da1e28", "N/A" = "gray")
  
  p_bar <- ggplot(barcode_long, aes(x = Antibiotic, y = isolate, fill = Prediction)) +
    geom_tile(color = "white", linewidth = 0.5) +
    scale_fill_manual(values = sir_cols) +
    labs(title = "Population Resistance Barcode", x = "Antibiotic", y = "Isolate") +
    theme_minimal() +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1, size=10, face="bold"),
      axis.text.y = element_text(family="mono", size=8),
      plot.title = element_text(face = "bold", size = 16, hjust = 0.5),
      legend.position = "bottom"
    )
    
  ggsave(file.path(output_dir, "barcode.png"), p_bar, width = 10, height = max(4, length(unique(barcode_long$isolate)) * 0.2), dpi = 300)
}

cat("Success\n")
