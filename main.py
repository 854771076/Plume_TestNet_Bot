# import requests
from web3 import Web3
from loguru import logger
import json,os
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed
from  fake_useragent import UserAgent
from eth_account.messages import encode_defunct
import requests
from datetime import timedelta,datetime
import time
from curl_cffi import requests
import threading
from functools import *
logger.add(
    "Plume_TestNet_Bot.log",
    rotation="1 week",
    retention="1 month",
    level="INFO",
    format="{time} {level} {message}",
    compression="zip"  # 轮换日志文件时进行压缩
)
def ckeck_one_day(func):
    def pass_func(name):
        logger.info(f'{name}-距离上次执行-{func.__name__}-还没有一天')
    def update_time(cls,key,wallet):
        wallet[key]=time.time()
        cls.update_wallet(wallet)
    @wraps(func)
    def wrapper(*args, **kwargs):
        this=args[0]
        key=func.__name__+'_ts'
        token=kwargs.get('token')
        
        if token:
            key+=f'_{token}'
        wallet=kwargs['wallet']
        ts=wallet.get(key)
        if not ts:
            func(*args, **kwargs)
            update_time(this,key,wallet)
            return 
        name=wallet['name']
        dt1 = datetime.fromtimestamp(ts)
        now = datetime.fromtimestamp(time.time())
        # 计算时间差
        time_difference = abs(now-dt1)
        if time_difference >= timedelta(days=1):
            func(*args, **kwargs)
            update_time(this,key,wallet)
            return 
        else:
            return pass_func(name)
    return wrapper
ua=UserAgent()
class Plume_TestNet_Bot:
    headers = {
            'Accept': 'application/json',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            # Already added when you pass json=
            # 'Content-Type': 'application/json',
            'Origin': 'https://miles.plumenetwork.xyz',
            'Pragma': 'no-cache',
            'Referer': 'https://miles.plumenetwork.xyz/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-site',
            'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }
    _lock=threading.Lock()
    def __init__(self,invited='RRU30',init=True,show_point=True,wallet_path='../wallets',contract_path='./contract',proxy_api='http://zltiqu.pyhttp.taolop.com/getip?count=10&neek=42670&type=2&yys=0&port=2&sb=&mr=1&sep=0&ts=1',rpc_url = 'https://testnet-rpc.plumenetwork.xyz/http'):
        self.proxy_api=proxy_api
        self.rpc_url=rpc_url
        self.wallet_path=wallet_path
        self.contract_path=contract_path
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.show_point=show_point
        self.invited=invited
        self.ip_pool=[]
        # 检查连接是否成功
        if not self.web3.is_connected():
            raise Exception("无法连接到 plumenet 节点")
        self.chain_id=161221135
        # 初始化钱包
        self.wallets=[]
        self.get_contract()
        logger.success(f'初始化智能合约成功：{self.contracts.keys()}')
        if init!=False:
            self.get_wallets()
            logger.success(f'初始化钱包成功-钱包数量：{len(self.wallets)}')
            
            self.init_accounts()
            self.show_inited_account()
    def get_sign(self,wallet,msg):
        # 账户信息
        private_key = wallet['private_key']
        address =wallet['address']
        # 使用web3.py编码消息
        message_encoded = encode_defunct(text=msg)
        # 签名消息
        signed_message = self.web3.eth.account.sign_message(message_encoded, private_key=private_key)
        # 打印签名的消息
        return signed_message.signature.hex()
    def check_balance(self,address):
        try:
            # 获取账户余额（单位是 Wei）
            balance={}
            balance_wei = self.web3.eth.get_balance(address)
            # 将余额从 Wei 转换为 Ether
            balance_ether = self.web3.from_wei(balance_wei, 'ether')
            balance['ETH']=round(float(balance_ether),5)
            response = requests.get(f'https://plume-testnet.explorer.caldera.xyz/api/v2/addresses/{address}/tokens', params={
                'type': 'ERC-20',
            }, headers=self.headers)
            data=response.json()['items']
            for token in data:
                balance[token['token']['symbol']]=round(int(token['value'])/(10**int(token['token']['decimals'])),5)
        except:
            pass
        return balance
    def get_NFTs(self,address):
        try:
            # 获取账户余额（单位是 Wei）
            balance={}
            response = requests.get(f'https://plume-testnet.explorer.caldera.xyz/api/v2/addresses/{address}/nft/collections', params={'type':''}, headers=self.headers)
            data=response.json()['items']
            for token in data:
                balance[token['token']['symbol']]={'id':int(token['token_instances'][0]['id']),'amount':int(token['amount'])}
        except:
            pass
        return balance
    def generate_and_save_wallet(self,filename):
        # 生成新账户
        account = self.web3.eth.account.create()
        # 获取地址和私钥
        address = account.address
        try:
            private_key = account.privateKey.hex()
        except:
            private_key = account._private_key.hex()
        # 将地址和私钥保存到 JSON 文件
        wallet_info = {
            'address': address,
            'private_key': private_key
        }
        with open(filename, 'w') as file:
            json.dump(wallet_info, file, indent=4)
        logger.success(f"创建钱包成功-已保存到 {filename}")
    def load_wallet(self,filename):
        # 从 JSON 文件中读取钱包信息
        with open(filename, 'r') as file:
            wallet_info = json.load(file)
        wallet_name=filename.split('/')[-1].replace('.json','')
        wallet_info['name']=wallet_name
        wallet_info['balance']=self.check_balance(wallet_info['address'])
        wallet_info['NFTs']=self.get_NFTs(wallet_info['address'])
        wallet_info['init']=bool(wallet_info['balance']['ETH']>0)
        wallet_info['filename']=filename
        
        return wallet_info
    def load_contract(self,filename:str):
        # 从 JSON 文件中读取钱包信息
        with open(filename, 'r') as file:
            contract_info = json.load(file)
        return contract_info
    
    def update_wallet(self,wallet:dict,**params):
        filename=wallet.get('filename')
        for k,v in params.items():
            wallet[k]=v
        with open(filename, 'w') as file:
            json.dump(wallet, file, indent=4)
        logger.success(f"钱包信息已更新 {filename}")
        
    def get_wallets(self,max_workers=10):
        self.wallets=[]
        wallets_list = glob.glob(os.path.join(self.wallet_path, '*'))
        # 使用线程池来并发加载钱包
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.load_wallet, wallet) for wallet in wallets_list]

            for future in as_completed(futures):
                try:
                    wallet_data = future.result()
                    self.wallets.append(wallet_data)
                except Exception as e:
                    logger.error(f"Error loading wallet: {e}")
        return wallets_list
    def get_contract(self):
        self.contracts={}
        contracts_list = glob.glob(os.path.join(self.contract_path, '*'))
        # 使用线程池来并发加载钱包
        for contract_path in contracts_list:
            contract_info=self.load_contract(contract_path)
            name=contract_info.get('name')
            contract_address=contract_info.get('address')
            abi=contract_info.get('abi')
            contract_address=self.web3.to_checksum_address(contract_address)
            contract = self.web3.eth.contract(address=contract_address, abi=abi)
            self.contracts[name]=contract
    def create_wallets(self,num=1):
        index=len(self.wallets)+1
        for i in range(index,index+num):
            filename=os.path.join(self.wallet_path,f'wallet{i}.json')
            self.generate_and_save_wallet(filename)
            wallet=self.load_wallet(filename)
            self.wallets.append(
            wallet
            )
        time.sleep(5)
        self.init_accounts()

    def _empty_response(self):
        # 创建一个空响应对象
        response = requests.models.Response()
        response.status_code = 500  # 设置一个错误的状态码
        response._content = b'{}'  # 设置响应内容为空的 JSON 对象
        response.json = lambda: {}  # 设置 .json() 方法返回一个空字典
        return response
    def get_proxy(self):
        with self._lock:
            if not self.ip_pool:
                self.ip_pool=requests.get(f"{self.proxy_api}").json().get('data',[{}])
            try:
                data=self.ip_pool.pop()
            except:
                logger.error('本地ip，未有代理服务白名单，请更换代理或者开通白名单')
            proxy={'proxy':f'{data["ip"]}:{data["port"]}'}
            return proxy
    # def delete_proxy(self,proxy):
    #     requests.get(f"{self.proxy_api}/delete/?proxy={proxy}")
    def _get(self,url,headers,proxy=None):
        headers['User-Agent']=ua.chrome
        if not proxy:
            proxy = self.get_proxy().get("proxy")
        try:
            resp = requests.get(url, proxies={
                'http': "http://" + proxy,
                'https': "http://" + proxy
            },headers=headers, timeout=(30, 30),impersonate='edge99')
            # 使用代理访问
            # self.delete_proxy(proxy)
            return resp
        except Exception as e:
            logger.warning(f'请求失败正在重试：{e}')
        # 删除代理池中代理
        # self.delete_proxy(proxy)
        return self._empty_response()
    def _post(self,url,headers,json,proxy=None):

        headers['User-Agent']=ua.chrome
        if not proxy:
            proxy = self.get_proxy().get("proxy")
        try:

            resp = requests.post(url, proxies={
                'http': "http://" + proxy,
                'https': "http://" + proxy
            },json=json,headers=headers, timeout=(30, 30),impersonate='edge99')
            # self.delete_proxy(proxy)
            # 使用代理访问
            return resp
        except Exception as e:
            logger.warning(f'请求失败正在重试-{proxy}：{e}')
        # 删除代理池中代理
        # self.delete_proxy(proxy)
        return self._empty_response()
    def get_faucet_sign(self,wallet:dict,token:str='ETH'): 
        assert token in ('GOON','ETH')
        address=wallet.get('address')
        wallet_name=wallet.get('name')
        json_data = {
        'walletAddress': address,
        'token': token,
        }
        data={}
        while True:
            while data.get('walletAddress')!=wallet.get('address'):
                response = self._post('https://faucet.plumenetwork.xyz/api/faucet', headers=self.headers, json=json_data)
                if response.status_code>300:
                    logger.error(f'{wallet_name}:初始领水/签名异常，被反爬,resp:{response.text}') 
                try:           
                    data=response.json()
                except Exception as e:
                    logger.error(f'{wallet_name}:初始领水/签名异常,ERROR:{e}') 
                if data.get('walletAddress')==wallet.get('address'):
                    # self.update_wallet(wallet,**{f'signature_{token}':data[f'signature'],f'salt_{token}':data.get('salt')})
                    logger.success(f'{wallet_name}:初始领水/签名成功,resp:{response.text}')   
                    return data   
                else:
                    logger.error(f'{wallet_name}:初始领水/签名异常,代理ip被使用,resp:{response.text}')    
        
        
    
    def get_contract_transaction_gas_limit(self,func,address):
        # 估算所需的 gas
        gas_estimate = func.estimate_gas({
        'from': address
        })
        # 获取当前 gas 价格
        gas_price = self.web3.eth.gas_price
        # 获取账户余额
        balance = self.web3.eth.get_balance(address)
        # 计算总费用
        total_cost = gas_estimate * gas_price
        # 判断 gas 或转账是否合理
        if total_cost > balance:
            ValueError('gas不足改日领水后重试')
        # 返回估算的 gas
        return gas_estimate
    def run_contract(self, func, wallet):
        with self._lock:
            try:
                gas_limit = self.get_contract_transaction_gas_limit(func, wallet['address'])
                nonce = self.web3.eth.get_transaction_count(wallet['address'])
                transaction = func.build_transaction({
                    'chainId': self.chain_id,
                    'gas': int(gas_limit * 1.1),
                    'gasPrice': int(self.web3.eth.gas_price * 1.2),
                    'nonce': nonce
                })
                signed_transaction = self.web3.eth.account.sign_transaction(transaction, private_key=wallet['private_key'])
                
                # 确保网络已准备好接收
                tx_hash = self.web3.eth.send_raw_transaction(signed_transaction.rawTransaction)
                
                # 等待交易被挖矿
                try:
                    status = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
                except Exception as e:
                    logger.warning(f"Error waiting for transaction receipt: {e}")
                    return tx_hash, None
                
                return tx_hash, status
            except Exception as e:
                if 'nonce too low' in str(e):
                    return self.run_contract(self, func, wallet)
                raise ValueError(f"Error in running contract function: {e}")
                
            
                
    def approve(self,wallet,spender='0x4c722a53cf9eb5373c655e1dd2da95acc10152d1',value=100000,token='GOON',NFT=False,tokenId=287085):
        name=wallet['name']
        token_contract=self.contracts[token]
        spender=self.web3.to_checksum_address(spender)
        try:
            if NFT:
                func=token_contract.functions.approve(spender,tokenId)
                tx_hash,receipt=self.run_contract(func,wallet)
                
            else:
                decimals = token_contract.functions.decimals().call()
                value=int(value * (10 ** decimals))
                func=token_contract.functions.approve(spender,value)
                tx_hash,receipt=self.run_contract(func,wallet)
            logger.success(f'{name}-授权成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
        except Exception as e:
            raise ValueError(f'{name}-授权失败-ERROR：{e}')
    # @ckeck_one_day
    def swap(self,wallet,base='gnUSD',quote:str='GOON',amount_in_base_currency=0.1,pool_idx = 36000,limit_price=65537,is_buy = False,in_base_qty = False,tip=0,reserve_flags = 0):
        self.get_wallets()
        if reserve_flags==0:
            if amount_in_base_currency>wallet['balance'][quote]:
                amount_in_base_currency=0.9*wallet['balance'][quote]
                assert amount_in_base_currency<=wallet['balance'][quote],f"{quote}余额不足，交换：{amount_in_base_currency}，余额：{wallet['balance'][quote]}"
        else:
            if amount_in_base_currency>wallet['balance'][base]:
                amount_in_base_currency=0.9*wallet['balance'][base]
                assert amount_in_base_currency<=wallet['balance'][base],f"{base}余额不足，交换：{amount_in_base_currency}，余额：{wallet['balance'][quote]}"
        name=wallet['name']
        base_contract=self.contracts[base]
        quote_contract=self.contracts[quote]
        swap_contract=self.contracts['swap']
        quote_decimals = quote_contract.functions.decimals().call()
        base_decimals = base_contract.functions.decimals().call()
        # 设置交易参数
        base = self.web3.to_checksum_address(base_contract.address)
        quote =self.web3.to_checksum_address(quote_contract.address)
        # 根据代币精度调整交易数量
        qty = int(amount_in_base_currency * (10 ** base_decimals))
        min_out = int(0.98 * (10 ** quote_decimals))  # 最小输出
        try:
            func=swap_contract.functions.swap(base, quote, pool_idx, is_buy, in_base_qty, qty, tip, limit_price, min_out, reserve_flags)
            tx_hash,receipt = self.run_contract(func,wallet)
            logger.success(f'{name}-交换成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
        except Exception as e:
            raise ValueError(f'{name}交换失败-ERROR：{e}')
    # @ckeck_one_day
    def checkin(self,wallet:dict):
        checkin_func=self.contracts['checkin'].functions.checkIn()
        # 构建交易
        name=wallet['name']
        try:
            tx_hash,receipt = self.run_contract(checkin_func,wallet)
            logger.success(f'{name}签到成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
            wallet['checkin_time']=time.time()
        except Exception as e:
            raise ValueError(f'{name}签到失败-ERROR：{e}')
    def login(self,wallet):
        '''
        登录官网
        '''
        name=wallet['name']
        address=wallet['address']
        # 获取当前时间
        current_time = datetime.utcnow()
        # 格式化为指定格式
        formatted_time = current_time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
        msg=f'miles.plumenetwork.xyz wants you to sign in with your Ethereum account:\n{address}\n\nPlease sign with your account\n\nURI: https://miles.plumenetwork.xyz\nVersion: 1\nChain ID: 161221135\nNonce: HKpU4qEEiuiyb6kUH\nIssued At: {formatted_time}'
        signature=self.get_sign(wallet,msg)
        json_data = {
            'message':msg,
            'signature': signature,
            'referrer': self.invited,
            'strategy': 'web3',
        }
        while True:
            response = self._post('https://points-api.plumenetwork.xyz/authentication', headers=self.headers, json=json_data)
            data=response.json()
            if data.get('accessToken'):
                self.update_wallet(wallet,**data)
                logger.success(f'{name}-登录成功')
                break
            else:
                logger.error(f'{name}-登录失败,重新登录中-ERROR：{data}')
    # @ckeck_one_day
    def get_faucet(self,wallet:dict,token='ETH'):
        assert token in ('GOON','ETH')
        data=self.get_faucet_sign(wallet=wallet,token=token)

        token = token
        salt = self.web3.to_bytes(hexstr=data['salt'])  # 确保是32字节的十六进制字符串
        signature = self.web3.to_bytes(hexstr=data['signature'])  # 签名的十六进制字符串
        faucet_func=self.contracts['faucet'].functions.getToken(token, salt, signature)
        # 构建交易
        name=wallet['name']
        try:
            tx_hash,receipt = self.run_contract(faucet_func,wallet)
            logger.success(f'{name}领水成功-{token}-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
        except Exception as e:
            raise ValueError(f'{name}领水失败-{token}-ERROR：{e}')
    def show_inited_account(self):
        print_str=f'\n{"index":<3}\t{"name":<10}\t{"points":<8}\t{"NFT":<30}\t{"balance":<80}\n'
        for wallet in self.wallets:
            name=wallet['name'].split('\\')[-1].replace('.json','')
            print_str+=f"{self.wallets.index(wallet):<3}\t{name:<10}\t{wallet.get('user',{}).get('totalPoints',0):<8}\t{str(wallet.get('NFTs')):<30}\t{str(wallet.get('balance')):<80}\n"
        if not self.wallets:
            print_str+='暂无钱包，请创建...'
        logger.success(print_str)
    # @ckeck_one_day
    def stake(self,wallet,value=50):
        self.get_wallets()
        assert value<=wallet['balance']['gnUSD'],f'gnUSD余额不足，质押：{value}，余额：{wallet["balance"]["gnUSD"]}'
        name=wallet['name']
        stake_contract=self.contracts['stake']
        gnUSD_decimals = self.contracts['gnUSD'].functions.decimals().call()
        # 根据代币精度调整交易数量
        value = int(value * (10 ** gnUSD_decimals))
        func=stake_contract.functions.stake(value)
        try:
            tx_hash,receipt = self.run_contract(func,wallet)           
            logger.success(f'{name}-质押成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
        except Exception as e:
            raise ValueError(f'{name}-质押失败-ERROR：{e}')
    def check_Kuma(self,wallet):
        NTFS=self.get_NFTs(wallet['address'])
        kuma_ID=[]
        for key in NTFS.keys():
            if 'kuma' in key.lower():
                kuma_ID.append(wallet['NFTs'][key]['id'])
        return kuma_ID

    def init_account(self,wallet:dict):
        name=wallet['name'] 
        if not wallet.get('init_approve'):
            self.get_faucet_sign(wallet,'ETH')
            self.get_wallets()
            self.approve(wallet)
            self.approve(wallet,spender='0xA34420e04DE6B34F8680EE87740B379103DC69f6',token='gnUSD')
            wallet['init_approve']=True
            self.update_wallet(wallet=wallet)
        
        if self.show_point:
            self.login(wallet)    
        logger.success(f'{name}初始化成功')
    def daily_task(self,wallet):
        try:
            self.checkin(wallet=wallet)
        except Exception as e:
            logger.warning(f"{wallet.get('name')}-当日已签到或错误-{e}")
        try:
            self.get_faucet(wallet=wallet,token='ETH')
        except Exception as e:
            logger.warning(f"{wallet.get('name')}-当日已领水ETH或错误-{e}") 
        try:
            self.get_faucet(wallet=wallet,token='GOON')
        except Exception as e:
            logger.warning(f"{wallet.get('name')}-当日已领水GOON或错误-{e}") 

        count=5
        while count>0:
            try:
                self.swap(wallet=wallet)
                break
            except Exception as e:
                logger.warning(f"{wallet.get('name')}-swap失败，等待重试-{e}")
                time.sleep(60*2)
            finally:
                count-=1
        count=5
        while count>0:
            try:
                self.stake(wallet=wallet)
                break
            except Exception as e:
                logger.warning(f"{wallet.get('name')}-stake失败，等待重试-{e}")
                time.sleep(60*2)
            finally:
                count-=1
        try:
            self.mint_Kuma(wallet=wallet)
        except Exception as e:
            logger.warning(f"{e}")

        try:
            self.swap_Kuma(wallet=wallet)
        except Exception as e:
            logger.warning(f"{e}")
        
    # @ckeck_one_day
    def mint_Kuma(self,wallet):
        name=wallet['name']
        aick_contract=self.contracts['Kuma']
        func=aick_contract.functions.mintAICK()
        try:
            tx_hash,receipt = self.run_contract(func,wallet)            
            logger.success(f'{name}-Kuma mint成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
            kuma=self.check_Kuma(wallet)
            # 授权
            init=[]
            if kuma:
                for Id in kuma:
                    if Id not in wallet.get('kuma_ntf_init_list',[]):
                        self.approve(wallet,spender='0xa4e9ddad862a1b8b5f8e3d75a3aad4c158e0faab',token='Kuma-AICK',NFT=True,tokenId=Id)
                        init.append(Id)
                new=wallet.get('kuma_ntf_init_list',[])+init
                wallet['kuma_ntf_init_list']=new
                self.update_wallet(wallet)
        except Exception as e:
            raise ValueError(f'{name}-Kuma mint失败-ERROR：{e}')
    # @ckeck_one_day
    def swap_Kuma(self,wallet):
        name=wallet['name']
        aick_contract=self.contracts['Kuma-SWAP']
        try:
            tokenId=self.check_Kuma(wallet).pop()
            func=aick_contract.functions.sellBond(tokenId)
            tx_hash,receipt = self.run_contract(func,wallet)            
            logger.success(f'{name}-AICK swap成功-Transaction-交易哈希: {tx_hash.hex()}-交易状态: {receipt.status}')
        except Exception as e:
            raise ValueError(f'{name}-AICK swap失败-ERROR：{e}')
    def init_accounts(self,max_workers=10):
        self.get_wallets()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.init_account, wallet) for wallet in self.wallets]
            for future in as_completed(futures):
                try:
                    data = future.result()
                except Exception as e:
                    logger.error(f"Error init wallet: {e}")
        
        self.get_wallets()
    def do_daily_tasks(self,max_workers=10):
        self.get_wallets()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.daily_task, wallet) for wallet in self.wallets]
            for future in as_completed(futures):
                try:
                    data = future.result()
                except Exception as e:
                    logger.error(f"Error daily_task wallet: {e}")
        
        self.get_wallets()
        self.show_inited_account()
if __name__=='__main__':      
    bot=Plume_TestNet_Bot(show_point=True)
    # bot.mint_Kuma(wallet=bot.wallets[0])
    # bot.swap_Kuma(wallet=bot.wallets[0])
    # bot.create_wallets(1)
    bot.do_daily_tasks(max_workers=1)
    # bot.swap(bot.wallets[0])
