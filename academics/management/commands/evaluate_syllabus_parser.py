import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from academics.evaluation import DEFAULT_CASES, evaluate_cases


class Command(BaseCommand):
    help = "Evaluate the local parser against labeled syllabus fixtures, without network access."

    def add_arguments(self, parser):
        parser.add_argument("--cases", default=str(DEFAULT_CASES))
        parser.add_argument("--report", help="Optional path to write the JSON evaluation report.")

    def handle(self, *args, **options):
        report = evaluate_cases(options["cases"])
        if options["report"]:
            Path(options["report"]).write_text(json.dumps(report, indent=2), encoding="utf-8")
        self.stdout.write(report["scope"])
        self.stdout.write(f"Passed {report['passed']}/{report['total']} cases.")
        for result in report["results"]:
            if not result["passed"]:
                self.stdout.write(json.dumps(result, ensure_ascii=False))
        if report["passed"] != report["total"]:
            raise CommandError("Syllabus regression failures found.")
