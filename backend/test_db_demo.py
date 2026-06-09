"""Test script for MVP Database Setup."""

import sys
from pathlib import Path

# Ensure root is in sys path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database.session import engine, SessionLocal
from backend.database.models import (
    Base, User, Project, ReferenceDatabase, DatabaseVersion,
    Sample, AnalysisJob, AMRGene, AMRHit
)

def main():
    print("=== Testing MVP Database Architecture ===")
    
    print("\n[1] Initializing Database & Creating Tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    
    db = SessionLocal()
    
    try:
        import uuid
        test_id = uuid.uuid4().hex[:8]
        
        print(f"\n[2] Seeding Stub Data (Users, Projects, References) for run {test_id}...")
        # Create a mock user
        user = User(email=f"test_{test_id}@vetgenomehub.com", username=f"testuser_{test_id}", password_hash="hash")
        db.add(user)
        db.commit()
        
        # Create a mock project
        project = Project(name=f"Demo Project {test_id}", slug=f"demo-proj-{test_id}", owner_id=user.id)
        db.add(project)
        db.commit()
        
        # Create a reference database & version
        ref_db = ReferenceDatabase(name=f"CARD {test_id}", short_code=f"CARD_{test_id}", data_type="AMR")
        db.add(ref_db)
        db.commit()
        
        db_ver = DatabaseVersion(db_id=ref_db.id, version=f"v3.2.5-{test_id}")
        db.add(db_ver)
        db.commit()
        
        print(f" -> Created User: {user.username} (ID: {user.id})")
        print(f" -> Created Project: {project.name} (ID: {project.id})")
        print(f" -> Created DB Version: CARD {db_ver.version} (ID: {db_ver.id})")
        
        print("\n[3] Creating MVP Domain Data (Sample, Job, AMR Results)...")
        # Create a sample
        sample_isolate = f"E.coli_O157_{test_id}"
        sample = Sample(project_id=project.id, isolate_name=sample_isolate, species="Escherichia coli", submitter_id=user.id)
        db.add(sample)
        db.commit()
        
        # Create a job
        job = AnalysisJob(sample_id=sample.id, project_id=project.id, submitted_by=user.id)
        db.add(job)
        db.commit()
        
        # Create an AMR Gene (Result from Engine)
        amr_gene = AMRGene(
            sample_id=sample.id, job_id=job.id, db_version_id=db_ver.id,
            gene_name="blaCTX-M-15", drug_class="cephalosporin",
            confidence_tier="HIGH", confidence_score=0.99
        )
        db.add(amr_gene)
        db.commit()
        
        # Create an AMR Hit (Detailed tool match)
        amr_hit = AMRHit(
            amr_gene_id=amr_gene.id, detection_tool="AMRFinderPlus",
            hit_category="Perfect", identity_pct=100.0, coverage_pct=100.0,
            contig_id="contig_1", contig_start=150, contig_end=1025
        )
        db.add(amr_hit)
        db.commit()
        
        print(" -> Data successfully inserted.")
        
        print("\n[4] Querying Data via Relationships...")
        # Fetch the sample and use relationships to fetch its AMR genes
        retrieved_sample = db.query(Sample).filter(Sample.isolate_name == sample_isolate).first()
        print(f"Retrieved Sample: {retrieved_sample.isolate_name} (Species: {retrieved_sample.species})")
        
        genes = db.query(AMRGene).filter(AMRGene.sample_id == retrieved_sample.id).all()
        for g in genes:
            print(f" -> Found Gene: {g.gene_name} (Drug Class: {g.drug_class})")
            for h in g.hits:
                print(f"    -> Supported by Hit: {h.hit_category} on {h.contig_id} ({h.identity_pct}% ID)")
        
        print("\n=== All Database Tests Passed ===")
        
    except Exception as e:
        print(f"\n[ERROR] Test failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        engine.dispose()
        # The user requested NOT to delete the database file, so we leave amr_mvp.db intact.

if __name__ == "__main__":
    main()
