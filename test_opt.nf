nextflow.enable.dsl=2
process myproc {
    input:
    tuple val(id), path(file1, optional: true)
    script:
    """
    echo "ID: \$id, file1: \$file1"
    """
}
workflow {
    ch = Channel.of(['sample1', null])
    myproc(ch)
}
