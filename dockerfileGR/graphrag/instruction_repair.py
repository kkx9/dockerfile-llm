from typing import List, Dict, Optional
import subprocess
import re
import openai


class DockerfileRepairService:
    def __init__(self, openai_api_key: str):
        openai.api_key = openai_api_key
        self.hadolint_rules = self._load_hadolint_rules()

    def _load_hadolint_rules(self) -> Dict[str, str]:
        """Load Hadolint rules and corresponding fixes"""
        return {
            "DL3000": "WORKDIR should use absolute paths - add '/' prefix to path",
            "DL3004": "Do not use sudo - replace with gosu",
            "DL3020": "Use COPY instead of ADD for files/directories",
            "DL3021": "COPY with more than 2 arguments requires last argument to end with /",
            "DL4004": "Multiple ENTRYPOINT instructions - only the last one will take effect",
            # Add more rules as needed
        }

    def _apply_hadolint_fixes(self, dockerfile: str) -> str:
        """Apply fixes based on Hadolint rules"""
        try:
            # Run Hadolint and capture output
            result = subprocess.run(
                ["hadolint", "-"],
                input=dockerfile.encode(),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                return dockerfile  # No errors found

            # Parse Hadolint output
            lines = result.stderr.split("\n")
            fixed_dockerfile = dockerfile.split("\n")

            for line in lines:
                if not line.strip():
                    continue

                # Example line: "DL3000 WORKDIR relative path should be absolute"
                match = re.match(r".*(DL\d+)\s+(.*)", line)
                if match:
                    rule_id = match.group(1)
                    if rule_id in self.hadolint_rules:
                        # Apply fix based on rule
                        if rule_id == "DL3000":
                            # Find WORKDIR line and make path absolute
                            for i, df_line in enumerate(fixed_dockerfile):
                                if df_line.strip().startswith("WORKDIR"):
                                    path = df_line.split("WORKDIR")[1].strip()
                                    if not path.startswith("/"):
                                        fixed_dockerfile[i] = f"WORKDIR /{path}"
                        elif rule_id == "DL3020":
                            # Replace ADD with COPY
                            for i, df_line in enumerate(fixed_dockerfile):
                                if df_line.strip().startswith("ADD"):
                                    fixed_dockerfile[i] = df_line.replace("ADD", "COPY")
                        # Add more rule handlers as needed

            return "\n".join(fixed_dockerfile)

        except Exception as e:
            print(f"Hadolint error: {e}")
            return dockerfile

    def _fix_build_errors(self, dockerfile: str, error_log: str) -> str:
        """Fix build errors using LLM"""
        prompt = f"""
        The following Dockerfile failed to build with this error:
        {error_log}

        Here is the Dockerfile:
        {dockerfile}

        Please fix the Dockerfile to resolve the build error while maintaining the original functionality.
        Return only the fixed Dockerfile content.
        """

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,  # Very low temperature for error fixes
            max_tokens=2000
        )

        return response.choices[0].message.content

    def repair_dockerfile(self, dockerfile: str) -> str:
        """Main method to repair Dockerfile"""
        # Step 1: Apply Hadolint static fixes
        fixed_dockerfile = self._apply_hadolint_fixes(dockerfile)

        # Step 2: Try to build and fix runtime errors
        try:
            build_result = subprocess.run(
                ["docker", "build", "-"],
                input=fixed_dockerfile.encode(),
                capture_output=True,
                text=True
            )

            if build_result.returncode != 0:
                fixed_dockerfile = self._fix_build_errors(fixed_dockerfile, build_result.stderr)

        except Exception as e:
            print(f"Build error: {e}")

        return fixed_dockerfile