import os
import logging
from document_processor import GenericDocumentIntelligence

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for local or Docker execution.
    Automatically sets correct input/output paths.
    """

    # Detect environment
    running_in_docker = os.path.exists("/.dockerenv")

    if running_in_docker:
        # Docker paths
        input_dir = "/app/input"
        output_dir = "/app/output"
    else:
        # Local paths
        input_dir = os.path.join(os.getcwd(), "input")
        output_dir = os.path.join(os.getcwd(), "output")

    try:
        processor = GenericDocumentIntelligence()
        processor.process_documents(input_dir, output_dir)
        print("✅ Processing completed successfully!")
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise


if __name__ == "__main__":
    main()
