from web3 import Web3
from eth_utils import keccak
from eth_abi.abi import encode
from eth_account import Account
from aiohttp import ClientResponseError, ClientSession, ClientTimeout
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime
from colorama import *
import asyncio, random, json, time, os, pytz

wib = pytz.timezone('Asia/Jakarta')

class Union:
    def __init__(self) -> None:
        self.headers = {
            "Accept": "application/graphql-response+json, application/json",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://app.union.build",
            "Referer": "https://app.union.build/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.GRAPHQL_API = "https://graphql.union.build/v1/graphql"
        self.SEPOLIA_RPC_URL = "https://sepolia.drpc.org/"
        self.HOLESKY_RPC_URL = "https://ethereum-holesky-rpc.publicnode.com/"
        self.SEI_RPC_URL = "https://evm-rpc-testnet.sei-apis.com/"
        self.CORN_RPC_URL = "https://21000001.rpc.thirdweb.com/"
        self.UCS03_ROUTER_ADDRESS = "0x5FbE74A283f7954f10AA04C2eDf55578811aeb03"
        self.BASE_TOKEN_ADDRESS = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
        self.ERC20_CONTRACT_ABI = json.loads('''[
            {"type":"function","name":"balanceOf","stateMutability":"view","inputs":[{"name":"address","type":"address"}],"outputs":[{"name":"","type":"uint256"}]}
        ]''')
        self.UCS03_CONTRACT_ABI = [
            {
                "inputs": [
                    { "internalType": "uint32", "name": "channelId", "type": "uint32" },
                    { "internalType": "uint64", "name": "timeoutHeight", "type": "uint64" },
                    { "internalType": "uint64", "name": "timeoutTimestamp", "type": "uint64" },
                    { "internalType": "bytes32", "name": "salt", "type": "bytes32" },
                    {
                        "components": [
                            { "internalType": "uint8", "name": "version", "type": "uint8" },
                            { "internalType": "uint8", "name": "opcode", "type": "uint8" },
                            { "internalType": "bytes", "name": "operand", "type": "bytes" },
                        ],
                        "internalType": "struct Instruction",
                        "name": "instruction",
                        "type": "tuple",
                    },
                ],
                "name": "send",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function",
            },
        ]
        self.xion_address = {}
        self.babylon_address = {}
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.used_rpc = 0
        self.tx_count = 0
        self.sepolia_amount = 0
        self.holesky_amount = 0
        self.sei_amount = 0
        self.corn_amount = 0
        self.min_delay = 0
        self.max_delay = 0

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Union Testnet{Fore.BLUE + Style.BRIGHT} Auto BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    def load_accounts(self):
        filename = "accounts.json"
        try:
            if not os.path.exists(filename):
                self.log(f"{Fore.RED}File {filename} Not Found.{Style.RESET_ALL}")
                return

            with open(filename, 'r') as file:
                data = json.load(file)
                if isinstance(data, list):
                    return data
                return []
        except json.JSONDecodeError:
            return []
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://api.proxyscrape.com/v4/free-proxy-list/get?request=display_proxies&proxy_format=protocolipport&format=text") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = [line.strip() for line in content.splitlines() if line.strip()]
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = [line.strip() for line in f.read().splitlines() if line.strip()]
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def generate_address(self, private_key: str):
        try:
            account = Account.from_key(private_key)
            address = account.address
            
            return address
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Generate Address Failed {Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                f"{Fore.YELLOW+Style.BRIGHT} {str(e)} {Style.RESET_ALL}                  "
            )
            return None
        
    def mask_account(self, account):
        try:
            mask_account = account[:6] + '*' * 6 + account[-6:]
            return mask_account
        except Exception as e:
            return None
        
    async def get_web3_with_check(self, address: str, use_proxy: bool, retries=3, timeout=60):
        request_kwargs = {"timeout": timeout}

        proxy = self.get_next_proxy_for_account(address) if use_proxy else None

        if use_proxy and proxy:
            request_kwargs["proxies"] = {"http": proxy, "https": proxy}

        for attempt in range(retries):
            try:
                web3 = Web3(Web3.HTTPProvider(self.used_rpc, request_kwargs=request_kwargs))
                web3.eth.get_block_number()
                return web3
            except Exception as e:
                if attempt < retries - 1:
                    await asyncio.sleep(3)
                    continue
                raise Exception(f"Failed to Connect to RPC: {str(e)}")
        
    async def get_token_balance(self, address: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)
            balance = web3.eth.get_balance(address)
            token_balance = balance / (10 ** 18)

            return token_balance
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None
        
    def pad_hex(self, value, length=64):
        return hex(value)[2:].zfill(length)

    def encode_hex_as_string(self, string, length=32):
        return string.lower()[2:].ljust(length * 2, '0')

    def encode_string_as_bytes(self, string, length):
        hex_str = string.encode('utf-8').hex()
        return hex_str.ljust(length * 2, '0')
        
    def generate_instruction_data(self, address: str, amount: int, pair: str):
        try:
            if pair == "Sepolia to Holesky":
                quote_token = "0x92b3bc0bc3ac0ee60b04a0bbc4a09deb3914c886"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(704) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(448) +
                    self.pad_hex(amount) +
                    self.pad_hex(512) +
                    self.pad_hex(576) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(640) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("ETH", 32) +
                    self.pad_hex(5) +
                    self.encode_string_as_bytes("Ether", 32) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(quote_token)
                )

            elif pair == "Sepolia to Babylon":
                quote_token = "0x62626e313837656178666171656d67336e7466656e356a6b73656c77706b367636357a353438393266327070746c78356733703971736d73633967683463"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(42) +
                    self.encode_string_as_bytes(self.babylon_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("ETH", 32) +
                    self.pad_hex(5) +
                    self.encode_string_as_bytes("Ether", 32) +
                    self.pad_hex(62) +
                    self.encode_hex_as_string(quote_token, 64)
                )

            elif pair == "Holesky to Sepolia":
                quote_token = "0xf6e7e2725b40ec8226036906cab0f5dc3722b8e7"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(704) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(448) +
                    self.pad_hex(amount) +
                    self.pad_hex(512) +
                    self.pad_hex(576) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(640) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("ETH", 32) +
                    self.pad_hex(5) +
                    self.encode_string_as_bytes("Ether", 32) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(quote_token)
                )

            elif pair == "Holesky to Xion":
                quote_token = "0x78696f6e317863397661687972726d33676d6c39787338396b3866753933673366736d35326a686a636b6d6778727a6c617a66307376303571366e75756e65"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(43) +
                    self.encode_string_as_bytes(self.xion_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("ETH", 32) +
                    self.pad_hex(5) +
                    self.encode_string_as_bytes("Ether", 32) +
                    self.pad_hex(63) +
                    self.encode_hex_as_string(quote_token, 64)
                )

            elif pair == "Holesky to Babylon":
                quote_token = "0x62626e31766a6172726e72716d366e63346a36303964746537677771666363706461643963776474747973356432737a6a717770377274736c726e373636"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(42) +
                    self.encode_string_as_bytes(self.babylon_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("ETH", 32) +
                    self.pad_hex(5) +
                    self.encode_string_as_bytes("Ether", 32) +
                    self.pad_hex(62) +
                    self.encode_hex_as_string(quote_token, 64)
                )

            elif pair == "Sei to Xion":
                quote_token = "0x78696f6e31746d733932636d33346c786c6e346b76787732786473676e63756d7a6570723565326575673930766d74797735357a38646a757176776e656537"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(43) +
                    self.encode_string_as_bytes(self.xion_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("SEI", 32) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("Sei", 32) +
                    self.pad_hex(63) +
                    self.encode_hex_as_string(quote_token, 64)
                )
            
            elif pair == "Sei to Corn":
                quote_token = "0xe86bed5b0813430df660d17363b89fe9bd8232d8"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(704) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(448) +
                    self.pad_hex(amount) +
                    self.pad_hex(512) +
                    self.pad_hex(576) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(640) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("SEI", 32) +
                    self.pad_hex(3) +
                    self.encode_string_as_bytes("Sei", 32) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(quote_token)
                )

            elif pair == "Corn to Xion":
                quote_token = "0x78696f6e31683734366464796b396339796834666363757a6b636d65703839776d6b356e357a6b773735373237336d71636d75656d633338733278746d7466"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(43) +
                    self.encode_string_as_bytes(self.xion_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(4) +
                    self.encode_string_as_bytes("BTCN", 32) +
                    self.pad_hex(7) +
                    self.encode_string_as_bytes("Bitcorn", 32) +
                    self.pad_hex(63) +
                    self.encode_hex_as_string(quote_token, 64)
                )
            
            elif pair == "Corn to Sei":
                quote_token = "0x92b3bc0bc3ac0ee60b04a0bbc4a09deb3914c886"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(704) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(448) +
                    self.pad_hex(amount) +
                    self.pad_hex(512) +
                    self.pad_hex(576) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(640) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(4) +
                    self.encode_string_as_bytes("BTCN", 32) +
                    self.pad_hex(7) +
                    self.encode_string_as_bytes("Bitcorn", 32) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(quote_token)
                )
            
            elif pair == "Corn to Babylon":
                quote_token = "0x62626e3170397a68377032667866337471766b306d64716e613273706b6a6c3030713230616a77656a34386d7a6d38327a6e61356e74377339707732706c"
                operand = (
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(32) +
                    self.pad_hex(1) +
                    self.pad_hex(3) +
                    self.pad_hex(96) +
                    self.pad_hex(768) +
                    self.pad_hex(320) +
                    self.pad_hex(384) +
                    self.pad_hex(480) +
                    self.pad_hex(amount) +
                    self.pad_hex(544) +
                    self.pad_hex(608) +
                    self.pad_hex(18) +
                    self.pad_hex(0) +
                    self.pad_hex(672) +
                    self.pad_hex(amount) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(address) +
                    self.pad_hex(42) +
                    self.encode_string_as_bytes(self.babylon_address[address], 64) +
                    self.pad_hex(20) +
                    self.encode_hex_as_string(self.BASE_TOKEN_ADDRESS) +
                    self.pad_hex(4) +
                    self.encode_string_as_bytes("BTCN", 32) +
                    self.pad_hex(7) +
                    self.encode_string_as_bytes("Bitcorn", 32) +
                    self.pad_hex(62) +
                    self.encode_hex_as_string(quote_token, 64)
                )

            instruction = {
                "version": 0,
                "opcode": 2,
                "operand": "0x" + operand
            }

            return instruction
        except Exception as e:
            raise Exception(f"Generate Instruction Data Failed: {str(e)}")

    async def perform_send(self, private_key: str, address: str, tx_amount: float, pair: str, use_proxy: bool):
        try:
            web3 = await self.get_web3_with_check(address, use_proxy)

            if pair == "Sepolia to Holesky":
                channel_id = 8
                fee = 1.5

            elif pair == "Sepolia to Babylon":
                channel_id = 7
                fee = 1.5
                
            elif pair == "Holesky to Sepolia":
                channel_id = 2
                fee = 0.001

            elif pair == "Holesky to Xion":
                channel_id = 4
                fee = 0.001

            elif pair == "Holesky to Babylon":
                channel_id = 3
                fee = 0.001

            elif pair == "Sei to Xion":
                channel_id = 1
                fee = 1.1

            elif pair == "Sei to Corn":
                channel_id = 2
                fee = 1.1
                
            elif pair == "Corn to Xion":
                channel_id = 2
                fee = 0.01

            elif pair == "Corn to Sei":
                channel_id = 3
                fee = 0.01

            elif pair == "Corn to Babylon":
                channel_id = 1
                fee = 0.01

            amount = web3.to_wei(tx_amount, "ether")
            timeout_height = 0
            timeout_timestamp = int(time.time() * 1_000_000_000) + 86_400_000_000_000
            timestamp_now = int(time.time())
            encoded_data = keccak(encode(["address", "uint256"], [address, timestamp_now]))
            salt = "0x" + encoded_data.hex()

            instruction = self.generate_instruction_data(address, amount, pair)
            
            token_contract = web3.eth.contract(address=web3.to_checksum_address(self.UCS03_ROUTER_ADDRESS), abi=self.UCS03_CONTRACT_ABI)

            send_data = token_contract.functions.send(channel_id, timeout_height, timeout_timestamp, salt, instruction)

            estimated_gas = send_data.estimate_gas({"from": address, "value":amount})
            latest_block = web3.eth.get_block("latest")
            base_fee = latest_block.get("baseFeePerGas", 0)
            max_priority_fee = web3.to_wei(fee, "gwei")
            max_fee = base_fee + max_priority_fee

            send_tx = send_data.build_transaction({
                "from": address,
                "value": amount,
                "gas": int(estimated_gas * 1.2),
                "maxFeePerGas": int(max_fee),
                "maxPriorityFeePerGas": int(max_priority_fee),
                "nonce": web3.eth.get_transaction_count(address, "pending"),
                "chainId": web3.eth.chain_id,
            })

            signed_tx = web3.eth.account.sign_transaction(send_tx, private_key)
            raw_tx = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_hash = web3.to_hex(raw_tx)
            receipt = await asyncio.to_thread(web3.eth.wait_for_transaction_receipt, tx_hash, timeout=300)
            block_number = receipt.blockNumber

            return tx_hash, block_number
        except Exception as e:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Message :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
            )
            return None, None
    
    async def print_timer(self):
        for remaining in range(random.randint(self.min_delay, self.max_delay), 0, -1):
            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Wait For{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} {remaining} {Style.RESET_ALL}"
                f"{Fore.BLUE + Style.BRIGHT}Seconds For Next Tx...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(1)

    def print_question(self):
        while True:
            try:
                print(f"{Fore.GREEN + Style.BRIGHT}Select Option:{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}1. Sepolia to Holesky{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Sepolia to Babylon{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Holesky to Sepolia{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}4. Holesky to Xion{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}5. Holesky to Babylon{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}6. Sei to Xion{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}7. Sei to Corn{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}8. Corn to Xion{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}9. Corn to Sei{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}10. Corn to Babylon{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}11. Random Pairs{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}12. Run 1, 5, 6, 9{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}13. Run All Pairs{Style.RESET_ALL}")
                option = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose -> {Style.RESET_ALL}").strip())

                if option in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]:
                    option_type = (
                        "Sepolia to Holesky" if option == 1 else 
                        "Sepolia to Babylon" if option == 2 else 
                        "Holesky to Sepolia" if option == 3 else 
                        "Holesky to Xion" if option == 4 else 
                        "Holesky to Babylon" if option == 5 else 
                        "Sei to Xion" if option == 6 else 
                        "Sei to Corn" if option == 7 else 
                        "Corn to Xion" if option == 8 else
                        "Corn to Sei" if option == 9 else
                        "Corn to Babylon" if option == 10 else
                        "Random Pairs" if option == 11 else
                        "Run 1, 5, 6, 9" if option == 12 else
                        "Run All Pairs"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{option_type} Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, or 13.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, or 13).{Style.RESET_ALL}")

        if option in [1, 2]:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        self.tx_count = tx_count
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    sepolia_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter ETH Sepolia Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if sepolia_amount > 0:
                        self.sepolia_amount = sepolia_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}ETH Sepolia Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if min_delay >= 0:
                        self.min_delay = min_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if max_delay >= min_delay:
                        self.max_delay = max_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        elif option in [3, 4, 5]:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        self.tx_count = tx_count
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    holesky_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter ETH Holesky Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if holesky_amount > 0:
                        self.holesky_amount = holesky_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}ETH Holesky Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if min_delay >= 0:
                        self.min_delay = min_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if max_delay >= min_delay:
                        self.max_delay = max_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        elif option in [6, 7]:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        self.tx_count = tx_count
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    sei_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter SEI Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if sei_amount > 0:
                        self.sei_amount = sei_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}SEI Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if min_delay >= 0:
                        self.min_delay = min_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if max_delay >= min_delay:
                        self.max_delay = max_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        elif option in [8, 9, 10]:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        self.tx_count = tx_count
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    corn_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter BTCN Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if corn_amount > 0:
                        self.corn_amount = corn_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}BTCN Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if min_delay >= 0:
                        self.min_delay = min_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if max_delay >= min_delay:
                        self.max_delay = max_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        else:
            while True:
                try:
                    tx_count = int(input(f"{Fore.YELLOW + Style.BRIGHT}How Many Times Do You Want To Make a Transfer? -> {Style.RESET_ALL}").strip())
                    if tx_count > 0:
                        self.tx_count = tx_count
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Please enter positive number.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    sepolia_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter ETH Sepolia Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if sepolia_amount > 0:
                        self.sepolia_amount = sepolia_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}ETH Sepolia Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    holesky_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter ETH Holesky Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if holesky_amount > 0:
                        self.holesky_amount = holesky_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}ETH Holesky Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    sei_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter SEI Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if sei_amount > 0:
                        self.sei_amount = sei_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}SEI Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    corn_amount = float(input(f"{Fore.YELLOW + Style.BRIGHT}Enter BTCN Amount for Each Transfers [1 or 0.01 or 0.001, etc in decimals] -> {Style.RESET_ALL}").strip())
                    if corn_amount > 0:
                        self.corn_amount = corn_amount
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}BTCN Amount must be greater than 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a float or decimal number.{Style.RESET_ALL}")

            while True:
                try:
                    min_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Min Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if min_delay >= 0:
                        self.min_delay = min_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= 0.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

            while True:
                try:
                    max_delay = int(input(f"{Fore.YELLOW + Style.BRIGHT}Max Delay Each Tx -> {Style.RESET_ALL}").strip())
                    if max_delay >= min_delay:
                        self.max_delay = max_delay
                        break
                    else:
                        print(f"{Fore.RED + Style.BRIGHT}Min Delay must be >= Min Delay.{Style.RESET_ALL}")
                except ValueError:
                    print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number.{Style.RESET_ALL}")

        while True:
            try:
                print(f"{Fore.WHITE + Style.BRIGHT}1. Run With Free Proxyscrape Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}2. Run With Private Proxy{Style.RESET_ALL}")
                print(f"{Fore.WHITE + Style.BRIGHT}3. Run Without Proxy{Style.RESET_ALL}")
                choose = int(input(f"{Fore.BLUE + Style.BRIGHT}Choose [1/2/3] -> {Style.RESET_ALL}").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "With Free Proxyscrape" if choose == 1 else 
                        "With Private" if choose == 2 else 
                        "Without"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}Run {proxy_type} Proxy Selected.{Style.RESET_ALL}")
                    break
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")

        return option, choose
    
    async def submit_tx_hash(self, tx_hash: str, proxy=None, retries=30):
        data = json.dumps({"query":"query GetPacketHashBySubmissionTxHash($submission_tx_hash: String!) {\n  v2_transfers(args: {p_transaction_hash: $submission_tx_hash}) {\n    packet_hash\n  }\n}","variables":{"submission_tx_hash":f"{tx_hash}"},"operationName":"GetPacketHashBySubmissionTxHash"})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        await asyncio.sleep(3)
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=120)) as session:
                    async with session.post(url=self.GRAPHQL_API, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        packet = result.get("data", {}).get("v2_transfers", [])
                        if packet == []:
                            raise ValueError("Packet Hash Is Empty")

                        return packet
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Message :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} {str(e)} {Style.RESET_ALL}"
                )

        return None
    
    async def process_perform_send(self, private_key: str, address: str, tx_amount: float, pair: int, use_proxy: bool):
        tx_hash, block_number = await self.perform_send(private_key, address, tx_amount, pair, use_proxy)
        if tx_hash and block_number:
            if pair in ["Sepolia to Holesky", "Sepolia to Babylon"]:
                explorer = f"https://sepolia.etherscan.io/tx/{tx_hash}"

            elif pair in ["Holesky to Sepolia", "Holesky to Xion", "Holesky to Babylon"]:
                explorer = f"https://holesky.etherscan.io/tx/{tx_hash}"

            elif pair in ["Sei to Xion", "Sei to Corn"]:
                explorer = f"https://seitrace.com/tx/{tx_hash}?chain=atlantic-2"

            elif pair in ["Corn to Xion", "Corn to Sei", "Corn to Babylon"]:
                explorer = f"https://testnet.cornscan.io/tx/{tx_hash}"
            
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                f"{Fore.GREEN+Style.BRIGHT} Perform Transfer Success {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Block   :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {block_number} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Explorer:{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {explorer} {Style.RESET_ALL}"
            )

            print(
                f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
                f"{Fore.YELLOW + Style.BRIGHT}Wait For Submiting Tx Hash...{Style.RESET_ALL}",
                end="\r",
                flush=True
            )
            await asyncio.sleep(5)

            proxy = self.get_next_proxy_for_account(address) if use_proxy else None

            submit = await self.submit_tx_hash(tx_hash, proxy)
            if submit:
                packet_hash = submit[0]["packet_hash"]

                union_explorer = f"https://app.union.build/explorer/transfers/{packet_hash}"

                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Submit  :{Style.RESET_ALL}"
                    f"{Fore.GREEN+Style.BRIGHT} Success {Style.RESET_ALL}                   "
                )
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Explorer:{Style.RESET_ALL}"
                    f"{Fore.WHITE+Style.BRIGHT} {union_explorer} {Style.RESET_ALL}"
                )
            else:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Submit  :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Failed {Style.RESET_ALL}                   "
                )
        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Perform On-Chain Failed {Style.RESET_ALL}"
            )

    async def process_option_1(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Sepolia to Holesky {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.SEPOLIA_RPC_URL
            tx_amount = self.sepolia_amount
            pair = "Sepolia to Holesky"
            ticker = "ETH Sepolia"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_2(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Sepolia to Babylon {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.SEPOLIA_RPC_URL
            tx_amount = self.sepolia_amount
            pair = "Sepolia to Babylon"
            ticker = "ETH Sepolia"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_3(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Holesky to Sepolia {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.HOLESKY_RPC_URL
            tx_amount = self.holesky_amount
            pair = "Holesky to Sepolia"
            ticker = "ETH Holesky"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_4(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Holesky to Xion {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.HOLESKY_RPC_URL
            tx_amount = self.holesky_amount
            pair = "Holesky to Xion"
            ticker = "ETH Holesky"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_5(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Holesky to Babylon {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.HOLESKY_RPC_URL
            tx_amount = self.holesky_amount
            pair = "Holesky to Babylon"
            ticker = "ETH Holesky"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_6(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Sei to Xion {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.SEI_RPC_URL
            tx_amount = self.sei_amount
            pair = "Sei to Xion"
            ticker = "SEI"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_7(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Sei to Corn {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.SEI_RPC_URL
            tx_amount = self.sei_amount
            pair = "Sei to Corn"
            ticker = "SEI"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_8(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Corn to Xion {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.CORN_RPC_URL
            tx_amount = self.corn_amount
            pair = "Corn to Xion"
            ticker = "BTCN"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_9(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Corn to Sei {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.CORN_RPC_URL
            tx_amount = self.corn_amount
            pair = "Corn to Sei"
            ticker = "BTCN"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_10(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Corn to Babylon {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            self.used_rpc = self.CORN_RPC_URL
            tx_amount = self.corn_amount
            pair = "Corn to Babylon"
            ticker = "BTCN"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_option_11(self, private_key: str, address: str, use_proxy: bool):
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Option :{Style.RESET_ALL}"
            f"{Fore.BLUE + Style.BRIGHT} Run Random Pairs {Style.RESET_ALL}                              "
        )
        for i in range(self.tx_count):
            self.log(
                f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{i+1}{Style.RESET_ALL}"
                f"{Fore.MAGENTA+Style.BRIGHT} Of {Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT}{self.tx_count}{Style.RESET_ALL}                                   "
            )

            pair = random.choice([
                "Sepolia to Holesky", "Sepolia to Babylon", "Holesky to Sepolia", 
                "Holesky to Xion", "Holesky to Babylon", "Sei to Xion",
                "Sei to Corn", "Corn to Xion", "Corn to Sei", "Corn to Babylon"
            ])

            if pair in ["Sepolia to Holesky", "Sepolia to Babylon"]:
                self.used_rpc = self.SEPOLIA_RPC_URL
                tx_amount = self.sepolia_amount
                ticker = "ETH Sepolia"

            elif pair in ["Holesky to Sepolia", "Holesky to Xion", "Holesky to Babylon"]:
                self.used_rpc = self.HOLESKY_RPC_URL
                tx_amount = self.holesky_amount
                ticker = "ETH Holesky"

            elif pair in ["Sei to Xion", "Sei to Corn"]:
                self.used_rpc = self.SEI_RPC_URL
                tx_amount = self.sei_amount
                ticker = "SEI"

            elif pair in ["Corn to Xion", "Corn to Sei", "Corn to Babylon"]:
                self.used_rpc = self.CORN_RPC_URL
                tx_amount = self.corn_amount
                ticker = "BTCN"

            balance = await self.get_token_balance(address, use_proxy)

            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Balance :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {balance} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Amount  :{Style.RESET_ALL}"
                f"{Fore.WHITE+Style.BRIGHT} {tx_amount} {ticker} {Style.RESET_ALL}"
            )
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}   Pair    :{Style.RESET_ALL}"
                f"{Fore.BLUE+Style.BRIGHT} {pair} {Style.RESET_ALL}"
            )

            if not balance or balance <= tx_amount:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}   Status  :{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Insufficient {ticker} Token Balance {Style.RESET_ALL}"
                )
                return
            
            await self.process_perform_send(private_key, address, tx_amount, pair, use_proxy)
            await self.print_timer()

    async def process_accounts(self, private_key: str, address: str, option: int, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        self.log(
            f"{Fore.CYAN + Style.BRIGHT}Proxy  :{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} {proxy} {Style.RESET_ALL}"
        )

        if option == 1:
            await self.process_option_1(private_key, address, use_proxy)

        elif option == 2:
            await self.process_option_2(private_key, address, use_proxy)

        elif option == 3:
            await self.process_option_3(private_key, address, use_proxy)

        elif option == 4:
            await self.process_option_4(private_key, address, use_proxy)

        elif option == 5:
            await self.process_option_5(private_key, address, use_proxy)

        elif option == 6:
            await self.process_option_6(private_key, address, use_proxy)

        elif option == 7:
            await self.process_option_7(private_key, address, use_proxy)

        elif option == 8:
            await self.process_option_8(private_key, address, use_proxy)

        elif option == 9:
            await self.process_option_9(private_key, address, use_proxy)

        elif option == 10:
            await self.process_option_10(private_key, address, use_proxy)

        elif option == 11:
            await self.process_option_11(private_key, address, use_proxy)

        elif option == 12:
            await self.process_option_1(private_key, address, use_proxy)

            await self.process_option_5(private_key, address, use_proxy)

            await self.process_option_6(private_key, address, use_proxy)

            await self.process_option_9(private_key, address, use_proxy)

        elif option == 13:
            await self.process_option_1(private_key, address, use_proxy)

            await self.process_option_2(private_key, address, use_proxy)

            await self.process_option_3(private_key, address, use_proxy)

            await self.process_option_4(private_key, address, use_proxy)

            await self.process_option_5(private_key, address, use_proxy)

            await self.process_option_6(private_key, address, use_proxy)

            await self.process_option_7(private_key, address, use_proxy)

            await self.process_option_8(private_key, address, use_proxy)

            await self.process_option_9(private_key, address, use_proxy)
            
            await self.process_option_10(private_key, address, use_proxy)

    async def main(self):
        try:
            accounts = self.load_accounts()
            if not accounts:
                self.log(f"{Fore.RED}No Accounts Loaded.{Style.RESET_ALL}")
                return
            
            option, use_proxy_choice = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice in [1, 2]:
                    use_proxy = True

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 22
                for idx, account in enumerate(accounts, start=1):
                    if account:
                        private_key = account["PrivateKey"]
                        xion_address = account["XionAddress"]
                        babylon_address = account["BabylonAddress"]
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {idx} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}Of{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {len(accounts)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )

                        if not private_key or not xion_address or not babylon_address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Account Data {Style.RESET_ALL}"
                            )
                            continue

                        address = self.generate_address(private_key)

                        if not address:
                            self.log(
                                f"{Fore.CYAN + Style.BRIGHT}Status :{Style.RESET_ALL}"
                                f"{Fore.RED + Style.BRIGHT} Invalid Private Key or Library Version Not Supported {Style.RESET_ALL}"
                            )
                            continue

                        self.xion_address[address] = xion_address
                        self.babylon_address[address] = babylon_address

                        self.log(f"{Fore.CYAN + Style.BRIGHT}Address:{Style.RESET_ALL}")

                        self.log(
                            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{address}{Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT} [EVM] {Style.RESET_ALL}"
                        )
                        self.log(
                            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{xion_address}{Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT} [XION] {Style.RESET_ALL}"
                        )
                        self.log(
                            f"{Fore.GREEN+Style.BRIGHT} ● {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{babylon_address}{Style.RESET_ALL}"
                            f"{Fore.BLUE+Style.BRIGHT} [BABYLON] {Style.RESET_ALL}"
                        )

                        await self.process_accounts(private_key, address, option, use_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*65)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")
            raise e

if __name__ == "__main__":
    try:
        bot = Union()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] Union Testnet - BOT{Style.RESET_ALL}                                       "                              
        )
