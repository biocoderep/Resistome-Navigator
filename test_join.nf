nextflow.enable.dsl=2
workflow {
    ch1 = Channel.of(['sample1', 'amr.json'])
    ch2 = Channel.empty()
    ch1.join(ch2, remainder: true).view()
}
