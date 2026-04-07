import os
import subprocess
import tempfile
import logging
from crewai.tools import BaseTool

logger = logging.getLogger(__name__)

class MermaidDiagramTool(BaseTool):
    """Generates an image or PDF from Mermaid Markdown syntax."""
    name: str = "generate_mermaid_diagram"
    description: str = (
        "Converts Mermaid text syntax into a visual diagram. "
        "Input: JSON with 'mermaid_code' (the raw text logic) and "
        "'output_format' (optional, one of: 'png', 'svg', 'pdf'. defaults to 'png')."
    )

    def _run(self, input_data: str) -> str:
        import json
        from datetime import datetime
        
        try:
            data = json.loads(input_data) if isinstance(input_data, str) else input_data
            mermaid_code = data.get("mermaid_code", "")
            ext = data.get("output_format", "png").lower()
            if ext not in ["png", "svg", "pdf"]:
                ext = "png"
                
            if not mermaid_code:
                return "Error: No mermaid_code provided."

            output_dir = "/app/outputs/diagrams"
            if not os.path.exists(output_dir):
                # Fallback if outside docker
                output_dir = os.path.join(os.getcwd(), "outputs", "diagrams")
                os.makedirs(output_dir, exist_ok=True)
                
            filename = f"diagram_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
            output_file = os.path.join(output_dir, filename)

            # Catalyst Works Dark Mode Theme Styling (Hex codes from brand references)
            catalyst_theme = '''%%{
  init: {
    "theme": "base",
    "themeVariables": {
      "primaryColor": "#1E293B",
      "primaryTextColor": "#F8FAFC",
      "primaryBorderColor": "#00B7C2",
      "lineColor": "#00B7C2",
      "secondaryColor": "#0F172A",
      "tertiaryColor": "#334155",
      "clusterBkg": "#0F172A",
      "clusterBorder": "#334155",
      "fontSize": "16px",
      "fontFamily": "Inter, Outfit, sans-serif"
    }
  }
}%%
'''
            # Ensure it doesn't already have an init block to avoid conflicts
            if "%%{init" not in mermaid_code:
                mermaid_code = catalyst_theme + mermaid_code

            # Write temp MMD file
            fd, temp_path = tempfile.mkstemp(suffix=".mmd")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(mermaid_code)

            # Detect mmdc executable path
            mmdc_path = os.path.join(os.getcwd(), "node_modules", ".bin", "mmdc.cmd" if os.name == "nt" else "mmdc")
            if not os.path.exists(mmdc_path):
                mmdc_path = "mmdc.cmd" if os.name == "nt" else "mmdc"
                
            try:
                cmd = [mmdc_path, "-i", temp_path, "-o", output_file, "-b", "transparent"]
                subprocess.run(cmd, check=True, capture_output=True, text=True, shell=(os.name == "nt"))
                
                os.remove(temp_path)
                return f"Diagram generated successfully: {output_file}"
                
            except subprocess.CalledProcessError as e:
                os.remove(temp_path)
                logger.error(f"Mermaid CLI failed: {e.stderr}")
                return f"Error running mmdc: {e.stderr}"

        except Exception as e:
            logger.error(f"MermaidDiagramTool failed: {e}")
            return f"Error: {e}"

mermaid_tool = MermaidDiagramTool()
