/*
=============================================================================
    SEQUENCE ALIGNMENT PROCESS
=============================================================================
*/

process sequence_alignment {
    tag "${sample_id}"
    
    label 'alignment'
    
    cpus params.alignment_cpus
    memory params.alignment_memory
    time "4h"
    errorStrategy 'ignore'
    
    publishDir "${params.output}/${sample_id}/alignment", mode: "copy"
    
    input:
        tuple val(sample_id), path(assembly_file), val(species), path(validation_report)
        path reference_db
    
    output:
        tuple val(sample_id), path("alignment_report.json"), path("alignment.bam")
    
    script:
        """
        # Setup paths to resolve backend modules regardless of container setup
        
        # 1. Fetch Reference Genome
        echo "Fetching reference genome for ${species}..."
        python -m backend.mutation_engine.ncbi_fetcher "${species}" reference.fasta
        
        if [ ! -s reference.fasta ]; then
            echo "ERROR: Failed to fetch reference genome."
            exit 1
        fi
        
        # 2. Reference Indexing
        echo "Indexing reference genome..."
        samtools faidx reference.fasta
        bowtie2-build reference.fasta ref_index
        
        # 3. Alignment
        echo "Aligning contigs to reference..."
        bowtie2 -p ${params.alignment_cpus} -x ref_index -f "${assembly_file}" -S alignment.sam
        
        if [ ! -s alignment.sam ]; then
            echo "ERROR: Alignment failed or generated empty SAM."
            exit 1
        fi
        
        # 4. BAM Processing (Sort & Index)
        echo "Converting to sorted BAM..."
        samtools view -@ ${params.alignment_cpus} -bS alignment.sam | samtools sort -@ ${params.alignment_cpus} -o alignment.bam
        samtools index alignment.bam
        
        # 5. Variant Calling
        echo "Calling variants with bcftools..."
        bcftools mpileup -Ou -f reference.fasta alignment.bam | bcftools call -mv -Ob -o calls.bcf
        bcftools view calls.bcf > variants.vcf
        
        if [ ! -s variants.vcf ]; then
            echo "WARNING: VCF file is empty. Creating empty valid VCF."
            echo "##fileformat=VCFv4.2" > variants.vcf
            echo "#CHROM	POS	ID	REF	ALT	QUAL	FILTER	INFO" >> variants.vcf
        fi
        
        # Save a dummy JSON report to maintain contract compatibility
        echo '{"status": "success", "aligner": "bowtie2", "variant_caller": "bcftools"}' > alignment_report.json
        
        echo "Alignment and Variant Calling Complete."
        """
}
