import requests
import logging
import os
from datetime import datetime, timedelta
import platform
import pytz 

class Panel:
    """
    A class for managing administration panel operations.

    Attributes:
        username (str): The username for authentication.
        password (str): The password for authentication.
        domain (str): The domain of the panel.
        port (int, optional): The port number for the panel API. Default is 443.
    """
    def __init__(self, username: str, password: str, domain: str, port: int = 443) -> None:
        """
        Initializes the Panel class.

        Args:
            username (str): The username for authentication.
            password (str): The password for authentication.
            domain (str): The domain of the panel.
            port (int, optional): The port number for the panel API. Default is 443.
        """
        self.username = username
        self.password = password
        self.domain = domain
        self.port = port
        
    def access_panel(self, username: str = None, password: str = None) -> dict :
        """
        Obtains access token for accessing the panel API.

        Args:
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.

        Returns:
            dict: A dictionary containing the access headers.
        """
        username = self.username or username
        password = self.password or password
        url = f'https://{self.domain}:{self.port}/api/admin/token'
        data = {
            'username': username,
            'password': password
        }
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            access_token = response.json()['access_token']
            access_headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {access_token}"
            }
            return access_headers
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred while obtaining access token: {e}')
            return False

    def get_users(self, username: str = None, password: str = None, user_status: str = None, access_panel: dict = None ) -> dict :
        """
        Retrieves the list of users from the panel.

        Args:
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.
            user_status (str, optional): Filter users by status (e.g., 'active', 'disabled'). Default is None.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            dict: A dictionary containing the list of users.
        """
        username = username or self.username
        password = password or self.password
        user_status = ('?status=' + user_status) if user_status in ['on_hold', 'disabled', 'active', 'expired', 'limited'] else ''  
        url = f'https://{self.domain}:{self.port}/api/users{user_status}'
        headers = access_panel or self.access_panel(username=username, password=password)
        try :
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            users_list = response.json()
            return users_list['users']
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred while retrieving users list: {e}')
            return False
    
    def delete_user(self, username: str, access_panel: dict = None ) -> bool :
        """
        Deletes a user from the panel.

        Args:
            username (str): The username of the user to be deleted.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            bool: True if the user is successfully deleted, False otherwise.
        """
        url = f'https://{self.domain}:{self.port}/api/user/{username}'
        headers = access_panel or self.access_panel()
        try:
            response = requests.delete(url, headers=headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred delete user: {e}')
            return False
        
    def users_statistics(self, username: str = None, password: str = None, users_list: dict = None, prefix: str = '', access_panel: dict = None ) -> str :
        """
        Generates statistics about users.

        Args:
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.
            users_list (dict, optional): A dictionary containing the list of users. If not provided, retrieves the list of users.
            prefix (str, optional): Filter users by username prefix. Default is an empty string.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            str: A formatted string containing the statistics.
        """ 
        username = username or self.username
        password = password or self.password
        headers = access_panel or self.access_panel(username=username, password=password)
        users_list = users_list or self.get_users(username=username, password=password, access_panel=headers)
        try :
            all_traffic_used, all_traffic_limit ,all_time_traffic_used, all_users = 0, 0, 0, 0
            users_count = {'active': 0,'on_hold': 0,'expired': 0,'limited': 0,'disabled': 0}
            for user in users_list:
                user_name = user['username']
                if user_name.startswith(prefix) :
                    all_users += 1
                    all_traffic_used += user['used_traffic'] or 0
                    all_traffic_limit += user['data_limit'] or 0
                    all_time_traffic_used += user['lifetime_used_traffic'] or 0
                    users_count[user['status']] += 1
            all_traffic_used = round((all_traffic_used / 1073741824), 3)
            all_traffic_limit = round((all_traffic_limit / 1073741824), 3)
            all_traffic_reaming = round((all_traffic_limit - all_traffic_used), 3)
            all_time_traffic_used = round((all_time_traffic_used / 1073741824), 3)            
            return f'\nadmin username: {username}\n' \
                f'all users: {all_users}\n' \
                f'active users: {users_count["active"]}\n' \
                f'expired users: {users_count["expired"]}\n' \
                f'limited users: {users_count["limited"]}\n' \
                f'on_hold users: {users_count["on_hold"]}\n' \
                f'disabled users: {users_count["disabled"]}\n' \
                f'all traffic used: {all_traffic_used} GB\n' \
                f'all traffic limited: {all_traffic_limit} GB\n' \
                f'all traffic reaming: {all_traffic_reaming} GB\n' \
                f'all time traffic used: {all_time_traffic_used} GB\n'
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred admin traffic: {e}')
            return False
            
    def calculation(self, calculation_type: str, data_limit: int, date_limit: int, traffic: int = 0, days: int = 0, coefficient_data: float = 1.0) -> int :
        """
        Performs calculation on data limit and date limit.

        Args:
            calculation_type (str): Type of calculation ('+' or '-').
            data_limit (int): The data limit.
            date_limit (int): The date limit.
            traffic (int, optional): The traffic to be added or subtracted. Default is 0.
            days (int, optional): The number of days to be added to the date limit. Default is 0.
            coefficient_data (float, optional): Coefficient for data limit calculation. Default is 1.0.

        Returns:
            tuple: A tuple containing the new data limit and date limit.
        """
        if calculation_type == '+' :
            data_limit = (float(data_limit) * float(coefficient_data)) + (float(traffic) * 1073741824)
            date_limit = (datetime.fromtimestamp(date_limit) + timedelta(days=float(days))).timestamp()
        elif calculation_type == '-' :
            data_limit = (float(data_limit) * float(coefficient_data)) - (float(traffic) * 1073741824)
            date_limit = (datetime.fromtimestamp(date_limit) + timedelta(days=float(days))).timestamp()
        else :
            raise ValueError(logging.error("❌\tInvalid calculation type. Use '+' or '-'"))
        return data_limit, date_limit
    
    def modify_user(self, modify_type: str, data: bool = 0, date: bool = 0, coefficient_data: float = 1.0, prefix: str = '', username: str = None, password: str = None, access_panel: dict = None ) -> str :
        """
        Modifies users' data limit and date limit.

        Args:
            modify_type (str): Type of modification ('+' or '-').
            data (bool, optional): The amount of data to be added or subtracted. Default is 0.
            date (bool, optional): The number of days to be added to the date limit. Default is 0.
            coefficient_data (float, optional): Coefficient for data limit calculation. Default is 1.0.
            prefix (str, optional): Filter users by username prefix. Default is an empty string.
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            str: A message indicating the success or failure of the modification process.
        """
        username = username or self.username
        password = password or self.password
        headers = access_panel or self.access_panel(username=username, password=password)
        users_list = self.get_users(username=username, password=password, user_status='active', access_panel=headers)
        try :
            if modify_type in ['+','-'] :
                for user in users_list :
                    username = user['username']
                    if username.startswith(prefix) :
                        data_limit = user['data_limit']
                        date_limit = user['expire']
                        data_used = user['used_traffic']
                        if data_limit is not None and date_limit is not None and data_used is not None:
                            new_data_limit, new_date_limit = self.calculation(calculation_type=modify_type, data_limit=data_limit, date_limit=date_limit, traffic=data, days=date, coefficient_data=coefficient_data)
                            url = f'https://{self.domain}:{self.port}/api/user/{username}'
                            user_details = {'data_limit': new_data_limit, 'expire': new_date_limit}
                            response = requests.put(url, json=user_details, headers=headers)
                            response.raise_for_status()
                            logging.info(f'🟢 user {username} is updated!')
                        else :
                            logging.info(f'🔵 Skipping user {username}.')
                logging.info(f'⚪\tThe process is done!\t{len(users_list)} is updated.')
            else :
                logging.warning('🔴 modify data is not currect')
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred modify data: {e}')
            return False
    
    def users_deleter(self, username: str = None, password: str = None, users_status: str = None, prefix: str = '', last_online: int = 0, access_panel: dict = None ) -> str :
        """
        Deletes users based on certain criteria.

        Args:
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.
            users_status (str, optional): Filter users by status (e.g., 'active', 'disabled'). Default is None.
            prefix (str, optional): Filter users by username prefix. Default is an empty string.
            last_online (int, optional): The threshold for last online time (in days). Default is 0.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            str: A message indicating the success or failure of the deletion process.
        """
        username = username or self.username
        password = password or self.password
        headers = access_panel or self.access_panel(username=username, password=password)
        users_status = users_status if users_status in ['on_hold', 'disabled', 'active', 'expired', 'limited'] else None  
        users_list = self.get_users(username=username, password=password, user_status=users_status, access_panel=headers)
        try :
            count_all, count_delete = 0, 0
            for user in users_list:
                user_name = user['username']
                if user_name.startswith(prefix) :
                    user_last_online = self.convert_to_secend(time_str=user['online_at']) or None
                    count_all += 1
                    if user_last_online and (user_last_online > (last_online * 86400)) :
                        user_delete = self.delete_user(username=user_name, access_panel=headers)
                        if user_delete :
                            logging.info(f'🟢 user {user_name} is deleted!')
                            count_delete += 1
                        else :
                            logging.error(f'🔴 user {user_name} is not deleted!')
            logging.info(f'⚪\tThe process is done!\tdelete {count_delete} user of {count_all} user')
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred users_deleter : {e}')
            return False

    def convert_to_secend(self, time_str: str) -> int :
        """
        Converts a datetime string to seconds.

        Args:
            time_str (str): The datetime string in ISO format.

        Returns:
            int: The equivalent time in seconds.
        """
        time = datetime.strptime(time_str, "%Y-%m-%dT%H:%M:%S.%f" if '.' in time_str else "%Y-%m-%dT%H:%M:%S")
        delta = datetime.now(pytz.timezone('Asia/Tehran')) - pytz.utc.localize(time).astimezone(pytz.timezone('Asia/Tehran'))
        return delta.days * 86400 + delta.seconds
    
    def change_status(self, get_user: str = 'active', new_status: str = 'disabled', prefix: str = '', username: str = None, password: str = None, access_panel: dict = None ) -> str :
        """
        Changes the status of users.

        Args:
            get_user (str, optional): The status of users to be modified (e.g., 'active', 'disabled'). Default is 'active'.
            new_status (str, optional): The new status for users (e.g., 'active', 'disabled'). Default is 'disabled'.
            prefix (str, optional): Filter users by username prefix. Default is an empty string.
            username (str, optional): The username for authentication. If not provided, uses the default username.
            password (str, optional): The password for authentication. If not provided, uses the default password.
            access_panel (dict, optional): Access headers for the panel API. If not provided, obtains access headers.

        Returns:
            str: A message indicating the success or failure of the status change process.
        """
        username = username or self.username
        password = password or self.password
        users_status = get_user if get_user in ['on_hold', 'disabled', 'active', 'expired', 'limited'] else 'active' 
        headers = access_panel or self.access_panel(username=username, password=password)
        users_list = self.get_users(username=username, password=password, user_status=users_status, access_panel=headers)
        try :
            count = 0
            for user in users_list :
                user_name = user['username']
                if user_name.startswith(prefix) :
                    count += 1
                    url = f'https://{self.domain}:{self.port}/api/user/{user_name}'
                    user_details = {'status': new_status}
                    response = requests.put(url, json=user_details, headers=headers)
                    response.raise_for_status()
                    logging.info(f'🟢 user {user_name} is updated!')
                else :
                    logging.info(f'🔵 Skipping user {user_name}.')
                logging.info(f'⚪\tThe process is done!\t{count} is updated.')
        except requests.exceptions.RequestException as e:
            logging.error(f'❌\tError occurred change status: {e}')
            return False
     
logging.basicConfig(level=logging.INFO, format='%(levelname)-8s->\t%(message)s')

def clear() -> None :
    os.system('cls') if platform.system() == 'Windows' else os.system('clear')

clear()

USERNAME = input('Please enter panel username: ')
PASSWORD = input('Please enter panel password: ')
DOMAIN = input('Please enter panel domain (without https and port): ')
PORT = int(input('Please enter panel port: '))

panel = Panel(
    username=USERNAME,
    password=PASSWORD,
    domain=DOMAIN,
    port=PORT)


clear()

if panel.access_panel() :
    while True :
        print('\n\tWelcome to Marzban_User_Manager\n')
        print('-' * 50)
        print('\n1) User statistics')
        print('\n2) Increase(+) or Decrease(-) Traffic to users')
        print('\n3) Increase(+) or Decrease(-) Days to users')
        print('\n4) Delete users with filters')
        print('\n5) Disabled/Activated users with filters')
        option_input = input('\nPlease Select an option number: ')
        option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
        clear()
        
        if option == 1 :
            print('Which one do you want user statistics based on?')
            print('\n\n1) All users')
            print('\n2) Users of an admin')
            print('\n3) Users with prefixes')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            if option == 1 :
                print('please wait...')
                print(panel.users_statistics())
            elif option == 2 :
                username = input('Please enter admin username: ')
                password = input('Please enter admin password: ')
                if len(username.split(' ')) == 1 and len(password.split(' ')) == 1 :
                    print('please wait...')
                    print(panel.users_statistics(username=username, password=password))
                else :
                    logging.error('❌\tnot currect, please try again.')
            elif option == 3 :
                prefix = input('Please enter a prefix: ')
                if len(prefix.split(' ')) == 1 :
                    print('please wait...')
                    print(panel.users_statistics(prefix=prefix))
                else :
                    logging.error('❌\tnot currect, please try again.')
            else :
                logging.error('❌\tnot currect, please try again.')

        elif option == 2 :
            print('Do you want to increase or decrease??')
            print('\n\n1) Increase (+)')
            print('\n2) Decrease (-)')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            modify_type = '+' if option == 1 else '-' 
            print('Do you want to add a coefficient or a number?')
            print('\n\n1) Number (like: 10 Gb, 25 Gb)')
            print('\n2) coefficient (like: 1.10, 2.0)')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            if option == 1:
                number_data = input('Please enter number (like 10, 25, 40): ')
                number_data = int(number_data) if len(number_data.split(' ')) == 1 else (logging.error('❌\tNot correct, please try again.') or exit())
                coefficient_data = 1.0
            elif option == 2:
                coefficient_data = input('Please enter coefficient (like 1.05, 1.22, 2.10): ')
                coefficient_data = float(coefficient_data) if len(coefficient_data.split(' ')) == 1 else (logging.error('❌\tNot correct, please try again.') or exit())
                number_data = 0
            
            clear()        
            print('Which category of users do you want to apply to?')
            print('\n\n1) All users')
            print('\n2) Users of an admin')
            print('\n3) Users with prefixes')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())        

            clear()
            if option == 1 :
                print('please wait...')
                panel.modify_user(modify_type=modify_type ,data=number_data, coefficient_data=coefficient_data)
            elif option == 2 :
                username = input('Please enter admin username: ')
                password = input('Please enter admin password: ')
                if len(username.split(' ')) == 1 and len(password.split(' ')) == 1 :
                    panel.modify_user(modify_type=modify_type, data=number_data, coefficient_data=coefficient_data)
                else :
                    logging.error('❌\tnot currect, please try again.')
            elif option == 3 :
                prefix = input('Please enter a prefix: ')
                if len(prefix.split(' ')) == 1 :
                    print('please wait...')
                    panel.modify_user(modify_type=modify_type, data=number_data, coefficient_data=coefficient_data, prefix=prefix)
                else :
                    logging.error('❌\tnot currect, please try again.')
            else :
                logging.error('❌\tnot currect, please try again.')

        elif option == 3 :
            print('Do you want to increase or decrease??')
            print('\n\n1) Increase (+)')
            print('\n2) Decrease (-)')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            modify_type = '+' if option == 1 else '-' 
            
            date_value = input('How much do you want to add (Days) (like: 10, 1, 5) ?')
            date_value = int(date_value) if date_value.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())

            print('Which category of users do you want to apply to?')
            print('\n\n1) All users')
            print('\n2) Users of an admin')
            print('\n3) Users with prefixes')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())        
            
            clear()
            if option == 1 :
                print('please wait...')
                panel.modify_user(modify_type=modify_type ,date=date_value)
            elif option == 2 :
                username = input('Please enter admin username: ')
                password = input('Please enter admin password: ')
                if len(username.split(' ')) == 1 and len(password.split(' ')) == 1 :
                    panel.modify_user(modify_type=modify_type, date=date_value, username=username, password=password)
                else :
                    logging.error('❌\tnot currect admin info, please try again.')
            elif option == 3 :
                prefix = input('Please enter a prefix: ')
                if len(prefix.split(' ')) == 1 :
                    print('please wait...')
                    panel.modify_user(modify_type=modify_type, date=date_value, prefix=prefix)
                else :
                    logging.error('❌\tnot currect prefix, please try again.')
            else :
                logging.error('❌\tnot currect option, please try again.')

        elif option == 4 :
            last_online_time = input("What is the minimum user's last online time(Days) (like: 1,5,10) ? ")
            last_online_time = int(last_online_time) if last_online_time.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            print('Users of which status should be deleted?')
            print('\n\n1) All status')
            print('\n2) Active')
            print('\n3) Disabled')
            print('\n4) Limited')
            print('\n5) Expired')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            status_texts = {1: None, 2: 'Active', 3: 'Disabled', 4: 'Limited', 5: 'Expired'}
            users_status = status_texts[option]
            clear()
            
            print('Which category of users do you want to delete?')
            print('\n\n1) From all users')
            print('\n2) From Users of an admin')
            print('\n3) From Users with prefixes')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()

            if option == 1 :
                print('please wait...')
                panel.users_deleter(users_status=users_status, last_online=last_online_time)
            elif option == 2 :
                username = input('Please enter admin username: ')
                password = input('Please enter admin password: ')
                if len(username.split(' ')) == 1 and len(password.split(' ')) == 1 :
                    panel.users_deleter(users_status=users_status, last_online=last_online_time, username=username, password=password)
                else :
                    logging.error('❌\tnot currect admin info, please try again.')
            elif option == 3 :
                prefix = input('Please enter a prefix: ')
                if len(prefix.split(' ')) == 1 :
                    print('please wait...')
                    panel.users_deleter(users_status=users_status, last_online=last_online_time, prefix=prefix)
                else :
                    logging.error('❌\tnot currect prefix, please try again.')
            else :
                logging.error('❌\tnot currect option, please try again.')

        elif option == 5:
            print('Do you want to increase or decrease??')
            print('\n\n1) activa to disabled')
            print('\n2) disabled to active')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())

            users_list_get = 'active' if option == 1 else 'disabled'
            user_new_status = 'disabled' if option == 1 else 'active'
            clear()
            
            print('Which category of users do you want to apply to?')
            print('\n\n1) Users of an admin')
            print('\n2) Users with prefixes')
            option_input = input('\nPlease Select an option number: ')
            option = int(option_input) if option_input.isdigit() else (logging.error("❌\tInvalid input! Please enter a valid integer.") or exit())
            clear()
            if option == 1 :
                username = input('Please enter admin username: ')
                password = input('Please enter admin password: ')
                if len(username.split(' ')) == 1 and len(password.split(' ')) == 1 :
                    panel.change_status(get_user=users_list_get, new_status=user_new_status, username=username, password=password)
                else :
                    logging.error('❌\tnot currect admin info, please try again.')
                    
            elif option == 2 :
                prefix = input('Please enter a prefix: ')
                if len(prefix.split(' ')) == 1 :
                    print('please wait...')
                    panel.change_status(get_user=users_list_get, new_status=user_new_status, prefix=prefix, username=username, password=password)
                else :
                    logging.error('❌\tnot currect prefix, please try again.')
            else :
                logging.error('❌\tnot currect option, please try again.')
        else :
            logging.error('❌\tnot currect option, please try again.')        
        want_continue = input('\n\n\tyou want continue (y/n)? ')
        if want_continue != 'y' :
            clear()
            break
else :
    print('\n\n\tYour Panel information is not currect, please try again.\n\n')
