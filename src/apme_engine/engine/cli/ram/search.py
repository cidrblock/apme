import argparse

from ...scanner import config
from ...risk_assessment_model import RAMClient
from ...utils import split_name_and_version


class RAMSearchCLI:
    args = None

    def __init__(self):
        parser = argparse.ArgumentParser(description="TODO")
        parser.add_argument("target_type", help="content type", choices={"ram"})
        parser.add_argument("action", help="action for RAM command or target_name of search action")
        parser.add_argument("target_name", help="target_name for the action")
        args = parser.parse_args()
        self.args = args

    def run(self):
        args = self.args
        action = args.action
        target_name = args.target_name
        if action != "search":
            raise ValueError('RAMSearchCLI cannot be executed without "search" action')

        ram_client = RAMClient(root_dir=config.data_dir)

        target_name, target_version = split_name_and_version(target_name)
        findings = ram_client.search_findings(target_name, target_version)
        if findings:
            print(findings.summary_txt)
