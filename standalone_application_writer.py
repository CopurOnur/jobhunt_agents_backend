"""
Standalone Interactive Application Writer CLI.
Allows users to provide their own CV and motivation letter, then customize them
for specific job applications through an interactive chat interface.
"""

import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

from agents import Runner, SQLiteSession

from job_agents.application_writer_agent import (
    create_interactive_application_writer_agent,
    load_user_materials_from_file,
    display_materials,
    save_interactive_session
)
from models import ApplicationMaterials


class InteractiveApplicationWriter:
    """Interactive CLI for customizing application materials."""

    def __init__(self):
        """Initialize the interactive application writer."""
        self.base_cv: Optional[str] = None
        self.base_motivation_letter: Optional[str] = None
        self.agent = None
        self.session = None
        self.current_materials: Optional[ApplicationMaterials] = None
        self.session_history = []

    def print_header(self):
        """Print welcome header."""
        print("\n" + "="*80)
        print("INTERACTIVE APPLICATION WRITER")
        print("Customize your CV and motivation letter for specific job applications")
        print("="*80 + "\n")

    def load_materials_interactive(self):
        """Interactively load user's base CV and motivation letter."""
        print("📄 Loading Your Base Materials\n")
        print("Choose how to provide your materials:")
        print("1. Load from files")
        print("2. Paste text directly")

        choice = input("\nYour choice (1 or 2): ").strip()

        if choice == "1":
            self._load_from_files()
        elif choice == "2":
            self._load_from_text()
        else:
            print("❌ Invalid choice. Please run again.")
            exit(1)

    def _load_from_files(self):
        """Load materials from files."""
        print("\n📁 Enter file paths:\n")
        cv_path = input("Path to your CV file: ").strip()
        letter_path = input("Path to your motivation letter file: ").strip()

        try:
            self.base_cv, self.base_motivation_letter = load_user_materials_from_file(
                cv_path, letter_path
            )
            print("\n✅ Materials loaded successfully!")
            print(f"   CV: {len(self.base_cv)} characters")
            print(f"   Motivation Letter: {len(self.base_motivation_letter)} characters")
        except FileNotFoundError as e:
            print(f"\n❌ Error: File not found - {e}")
            exit(1)
        except Exception as e:
            print(f"\n❌ Error loading files: {e}")
            exit(1)

    def _load_from_text(self):
        """Load materials from direct text input."""
        print("\n📝 Paste your CV (press Ctrl+D or Ctrl+Z when done):\n")
        cv_lines = []
        try:
            while True:
                line = input()
                cv_lines.append(line)
        except EOFError:
            pass

        self.base_cv = "\n".join(cv_lines)

        print("\n📝 Paste your motivation letter (press Ctrl+D or Ctrl+Z when done):\n")
        letter_lines = []
        try:
            while True:
                line = input()
                letter_lines.append(line)
        except EOFError:
            pass

        self.base_motivation_letter = "\n".join(letter_lines)

        print("\n✅ Materials captured successfully!")
        print(f"   CV: {len(self.base_cv)} characters")
        print(f"   Motivation Letter: {len(self.base_motivation_letter)} characters")

    def initialize_agent(self, job_description: str):
        """Initialize the agent with user's materials and job description."""
        print("\n🤖 Initializing AI Agent...\n")

        # Create agent with user's materials and job description
        self.agent = create_interactive_application_writer_agent(
            base_cv=self.base_cv,
            base_motivation_letter=self.base_motivation_letter,
            job_description=job_description
        )

        # Create session for conversation continuity
        session_id = f"interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.session = SQLiteSession(session_id=session_id, db_path="storage/sessions.db")

        print("✅ Agent initialized and ready!\n")

    async def get_job_description(self) -> tuple[str, str, str]:
        """
        Get job description from user.

        Returns:
            Tuple of (job_description, company_name, position_title)
        """
        print("="*80)
        print("JOB INFORMATION")
        print("="*80 + "\n")

        company_name = input("Company name: ").strip()
        position_title = input("Position title: ").strip()

        print("\n📝 Paste the job description (press Ctrl+D or Ctrl+Z when done):\n")
        job_lines = []
        try:
            while True:
                line = input()
                job_lines.append(line)
        except EOFError:
            pass

        job_description = "\n".join(job_lines)

        print(f"\n✅ Job information captured!")
        print(f"   Company: {company_name}")
        print(f"   Position: {position_title}")
        print(f"   Description: {len(job_description)} characters\n")

        return job_description, company_name, position_title

    async def generate_initial_materials(
        self,
        job_description: str,
        company_name: str,
        position_title: str
    ):
        """Generate initial customized materials."""
        print("🔄 Generating customized application materials...\n")

        prompt = f"""Generate customized application materials for this job:

Company: {company_name}
Position: {position_title}

Job Description:
{job_description}

Please customize my CV and motivation letter for this position."""

        try:
            result = await Runner.run(
                self.agent,
                prompt,
                session=self.session
            )

            self.current_materials = result.final_output_as(ApplicationMaterials)

            if self.current_materials:
                print("✅ Materials generated successfully!\n")
                display_materials(self.current_materials)

                # Add to history
                self.session_history.append({
                    "timestamp": datetime.now().isoformat(),
                    "type": "initial_generation",
                    "prompt": prompt,
                    "company": company_name,
                    "position": position_title
                })
            else:
                print("❌ Failed to generate materials. Please try again.")
                exit(1)

        except Exception as e:
            print(f"❌ Error generating materials: {e}")
            exit(1)

    async def refinement_loop(self):
        """Interactive refinement loop."""
        print("\n" + "="*80)
        print("REFINEMENT MODE")
        print("="*80)
        print("\nYou can now chat with the agent to refine your materials.")
        print("Examples:")
        print("  - 'Make the CV more technical'")
        print("  - 'Emphasize my leadership experience'")
        print("  - 'Shorten the motivation letter'")
        print("  - 'Add more about project management skills'")
        print("\nType 'save' to save and exit, 'show' to display current materials,")
        print("or 'quit' to exit without saving.\n")

        while True:
            user_input = input("💬 You: ").strip()

            if not user_input:
                continue

            if user_input.lower() == 'quit':
                print("\n👋 Exiting without saving...")
                break

            if user_input.lower() == 'save':
                await self.save_and_exit()
                break

            if user_input.lower() == 'show':
                if self.current_materials:
                    display_materials(self.current_materials)
                else:
                    print("❌ No materials to display yet.")
                continue

            # Process refinement request
            try:
                print("\n🔄 Processing your request...\n")

                result = await Runner.run(
                    self.agent,
                    user_input,
                    session=self.session
                )

                self.current_materials = result.final_output_as(ApplicationMaterials)

                if self.current_materials:
                    print("✅ Materials updated!\n")
                    display_materials(self.current_materials)

                    # Add to history
                    self.session_history.append({
                        "timestamp": datetime.now().isoformat(),
                        "type": "refinement",
                        "user_request": user_input
                    })
                else:
                    print("❌ Failed to update materials. Please try again.")

            except Exception as e:
                print(f"❌ Error: {e}")

    async def save_and_exit(self):
        """Save materials and exit."""
        if not self.current_materials:
            print("❌ No materials to save.")
            return

        print("\n💾 Saving application materials...\n")

        company_name = self.current_materials.company or "Unknown"

        try:
            file_paths = save_interactive_session(
                self.current_materials,
                company_name,
                session_history=self.session_history
            )

            print("\n✅ All materials saved successfully!")
            print(f"\n📁 Output directory: {file_paths['output_directory']}")
            print(f"   CV: {file_paths['cv_path']}")
            print(f"   Motivation Letter: {file_paths['letter_path']}")
            print(f"   Match Summary: {file_paths['summary_path']}")
            if 'history_path' in file_paths:
                print(f"   Session History: {file_paths['history_path']}")

            print("\n👋 Thank you for using Interactive Application Writer!")

        except Exception as e:
            print(f"❌ Error saving materials: {e}")

    async def run(self):
        """Run the interactive application writer."""
        self.print_header()

        # Step 1: Load base materials
        self.load_materials_interactive()

        # Step 2: Get job description
        job_description, company_name, position_title = await self.get_job_description()

        # Step 3: Initialize agent with job description
        self.initialize_agent(job_description)

        # Step 4: Generate initial materials
        await self.generate_initial_materials(job_description, company_name, position_title)

        # Step 5: Refinement loop
        await self.refinement_loop()


def main():
    """Main entry point for the standalone application writer."""
    try:
        writer = InteractiveApplicationWriter()
        asyncio.run(writer.run())
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted by user. Exiting...")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
