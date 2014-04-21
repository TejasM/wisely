import requests

__author__ = 'Cheng'

client_id = '0aff2449c24e7732ebfb8b50549faef7'
client_password = '243ab55db462a3f52fafb3bd1c50d75448f5aa74'

status_url = 'https://www.udemy.com/api-1.1/status'
root_url = 'https://www.udemy.com/api-1.1/'
headers = {'X-Udemy-Client-Id': '0aff2449c24e7732ebfb8b50549faef7',
           'X-Udemy-Client-Secret': '243ab55db462a3f52fafb3bd1c50d75448f5aa74'}


def check_udemy_api_status():
    client = requests.session()
    status_check = client.get(status_url, headers=headers).json()
    return status_check["status"] == 'OK'


def get_course(id):
    client = requests.session()
    course = client.get(root_url + 'courses/' + id, headers=headers).json()

    return course


def main():
    print(check_udemy_api_status)
    course = get_course('5678')

    return


if __name__ == '__main__':
    main()