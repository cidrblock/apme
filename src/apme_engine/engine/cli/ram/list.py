import argparse

from ...risk_assessment_model import RAMClient
from ...scanner import config
from ...utils import show_all_ram_metadata


class RAMListCLI:
    args = None

    def __init__(self):
        parser = argparse.ArgumentParser(description="TODO")
        parser.add_argument("target_type", help="content type", choices={"ram"})
        parser.add_argument("action", help="action for RAM command or target_name of search action")
        args = parser.parse_args()
        self.args = args

    def run(self):
        args = self.args
        action = args.action
        if action != "list":
            raise ValueError('RAMListCLI cannot be executed without "list" action')

        ram_client = RAMClient(root_dir=config.data_dir)

        all_ram_meta = ram_client.list_all_ram_metadata()
        show_all_ram_metadata(all_ram_meta)
