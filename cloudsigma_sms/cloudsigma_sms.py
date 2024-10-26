import requests
import random
import os
from bs4 import BeautifulSoup
from datetime import datetime
import colorama
import time
colorama.init()


ua = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"}
list_sum_of_phone = []



def get_phone_number(hist_num_path="./cloudsigma_sms/phone_hist.txt"):
    global list_sum_of_phone

    if not os.path.exists(hist_num_path):
        with open(hist_num_path, "a"): pass
    else:
        hist_phone = open(hist_num_path, "r")
        phone_number = hist_phone.read()
        r = requests.get(f"https://receive-smss.com/sms/{phone_number}/", headers=ua)
        hist_phone.close()

    list_random_phone = r.text.split("numberst = ")[1].split(";")[0].replace('[', '').replace(']', '').replace('"', '').replace('+', "").split(',')
    for phone in list_random_phone: list_sum_of_phone.append(phone) if phone not in list_sum_of_phone else 0
    
    with open(hist_num_path, "w") as file:
        file.write(random.choice(list_sum_of_phone))
    return phone_number


def get_all_messages(phone_number):
    phone_number = phone_number.replace("+", "")
    try:
        r = requests.get(f"https://receive-smss.com/sms/{phone_number}/", headers=ua)
        all_messages = []
        for message in r.text.split("<label>Message</label><br><span>")[1:-1]:
            message = BeautifulSoup(message, "html.parser")
            message = message.text
            all_messages.append(message.replace("\n", ""))
        return all_messages
    except Exception as e:
        return {"error": f"đã có lỗi khi truy vấn sdt -> {phone_number}"}



def check_cloudsigma_used():
    phone_number = get_phone_number()
    if "error" in phone_number:
        return phone_number
    all_messages = get_all_messages(phone_number)
    
    for message in all_messages:
        if message[:15] == "Your CloudSigma":
            phone_message = message.split("Sender")[0]
            return {"used": True, "phone_number": phone_number, "phone_message": phone_message, "message": f"sdt -> +{phone_number} đã dùng cho cloudsigma"}
        
    return {"used": False,"phone_number": phone_number, "message": f"sdt -> +{phone_number} chưa được dùng cho cloudsigma"}



def listen_new_message(phone_number):
    phone_number = phone_number.replace("+", "")
    times_count = 1
    while True:
        try:
            r = requests.get(f"https://receive-smss.com/sms/{phone_number}/", headers=ua)
            print(colorama.Fore.YELLOW + f"\r{times_count}s" + colorama.Style.RESET_ALL, end=" ")
            print(colorama.Fore.BLUE + f"đang chờ đợi tin nhắn mới từ -> +{phone_number}" + colorama.Style.RESET_ALL, end="")
            for message in r.text.split("<label>Message</label><br><span>")[1:3]:
                message = BeautifulSoup(message, "html.parser").text
                if message[:15] == "Your CloudSigma":
                    print()
                    return message
            times_count += 1
            time.sleep(1)
        except Exception as e:
            print(colorama.Fore.RED + f"đã có lỗi trong lần check tin nhắn này, sẽ thử lại, mã lỗi: {e}" + colorama.Style.RESET_ALL)
            continue


def check_uptime_of_phone(phone_number, min_month=2):
    headers = {
        "authority": "web.archive.org",
        "method": "GET",
        "path": f"/__wb/sparkline?output=json&url=https%3A%2F%2Freceive-smss.com%2Fsms%2F{phone_number}%2F&collection=web",
        "scheme": "https",
        "accept": "*/*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "vi,en;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "cookie": "donation-identifier=519bf7a1f4f1063352886b91502de4cd; abtest-identifier=43fe4b8e2d128c44d52ffd87df3f9fcd",
        "priority": "u=1, i",
        "referer": f"https://web.archive.org/web/20240000000000*/https://receive-smss.com/sms/{phone_number}/",
        "sec-ch-ua": "\"Microsoft Edge\";v=\"129\", \"Not=A?Brand\";v=\"8\", \"Chromium\";v=\"129\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36 Edg/129.0.0.0"
    }
    try:
        r = requests.get(
            f"https://web.archive.org/__wb/sparkline?output=json&url=https%3A%2F%2Freceive-smss.com%2Fsms%2F{phone_number}%2F&collection=web",
            headers=headers
        )
        response_json = r.json()
    
        if len(response_json['years']) > 1:
            return {"na": f"sdt -> +{phone_number} tồn tại hơn 1 năm, suy luận không phải phone mới nhất"}
        elif str(datetime.today().year) not in response_json['years']:
            return {"na": f"sdt -> +{phone_number} chỉ có một năm duy nhất, nhưng đã tồn tại lâu hơn hiện tại"}
        elif datetime.now().month - int(response_json['first_ts'][4:6]) > min_month:
            return {"na": f"sdt -> +{phone_number} được tạo cách thời gian hiện tại hơn {min_month} tháng, không phải mới nhất"}
        else:
            return {"good": phone_number, "message": f"sdt +{phone_number} đủ tiêu chí, hãy thử cho cloudsigma"}
    except Exception as e:
        return {"error": f"lỗi không xác định khi check uptime phone, mã lỗi {e}"}
    


def check_phone_log(phone_number):
    with open("./cloudsigma_sms/phone_log.txt", "r") as file:
        ds_sdt_log = file.read().splitlines()
    if f"+{phone_number}" in ds_sdt_log:
        return {"na": f"sdt -> +{phone_number} đã tồn tại trong log"}
    else:
        return {"good": f"sdt -> +{phone_number} chưa tồn tại trong log"}



def find_valid_phone():
    print(colorama.Fore.YELLOW + "[!] Dùng CTRL + C nếu muốn thoát khỏi chương trình smsonl" + colorama.Style.RESET_ALL)
    while True:
        try:
            check_clsm_used = check_cloudsigma_used()

            if "error" in check_clsm_used:
                print(colorama.Fore.RED + check_clsm_used['error'] + colorama.Style.RESET_ALL)
                continue
            elif check_clsm_used['used']:
                print(colorama.Fore.RED + check_clsm_used['message'] + colorama.Style.RESET_ALL)
            elif not check_clsm_used['used']:
                print(colorama.Fore.GREEN + check_clsm_used['message'] + colorama.Style.RESET_ALL)

            check_uptime = check_uptime_of_phone(check_clsm_used['phone_number'], min_month=1)

            if "na" in check_uptime:
                print(colorama.Fore.RED + check_uptime['na'] + colorama.Style.RESET_ALL)
            elif "good" in check_uptime:
                print(colorama.Fore.GREEN + check_uptime['message'] + colorama.Style.RESET_ALL)

            check_log = check_phone_log(check_clsm_used['phone_number'])

            if "na" in check_log:
                print(colorama.Fore.RED + check_log['na'] + colorama.Style.RESET_ALL)
            elif "good" in check_log:
                print(colorama.Fore.GREEN + check_log['good'] + colorama.Style.RESET_ALL)

            if not check_clsm_used['used'] and "good" in check_uptime and "good" in check_log:
                try:
                    with open("./cloudsigma_sms/phone_saved.txt", "a") as file:
                        file.write(f"+{check_clsm_used['phone_number']}\n")
                        print(colorama.Fore.GREEN + f"đã lưu thành công số -> {check_clsm_used['phone_number']}" + colorama.Style.RESET_ALL)
                    with open("./cloudsigma_sms/phone_log.txt", "a") as file:
                        file.write(f"+{check_clsm_used['phone_number']}\n")
                        print(colorama.Fore.GREEN + f"đã lưu thành công số -> {check_clsm_used['phone_number']} vào log" + colorama.Style.RESET_ALL)
                except:
                    print(colorama.Fore.RED + "đã có lỗi khi lưu sdt hơp lệ" + colorama.Style.RESET_ALL)

        except Exception as e:
            print(colorama.Fore.RED + f"đã có lỗi không xác định, mã lỗi {e}" + colorama.Style.RESET_ALL)
        except KeyboardInterrupt:
            print(colorama.Fore.GREEN + f"đã nhận CTRL+C, thoát khỏi phiên smsonl..." + colorama.Style.RESET_ALL)
            break


def listen_cloudsigma_message():
    print(colorama.Fore.YELLOW + "[!] Dùng CTRL+C nếu muốn thoát khỏi chương trình listen sms" + colorama.Style.RESET_ALL)
    phone_number_input = input(colorama.Fore.YELLOW + "nhập số điện thoại mà bạn muốn lắng nghe tin nhắn mới\n-> " + colorama.Style.RESET_ALL)
    try:
        message_output = listen_new_message(phone_number_input)
    except KeyboardInterrupt:
        print()
        print(colorama.Fore.GREEN + f"đã nhận CTRL+C, thoát khỏi phiên listen sms..." + colorama.Style.RESET_ALL)
        return 0
    
    message_output = message_output.strip()
    message_output = message_output.replace("Time", "Time -> ")
    message_output = message_output.replace("Sender", "Sender -> ")
    message_output_lines = message_output.splitlines()
    m = ""
    m += f"| {message_output_lines[0]} |\n"
    m += f"| {message_output_lines[1]}                                |\n"
    if len(message_output_lines[2]) == 20:
        m += f"| {message_output_lines[2]}                                |"
    elif len(message_output_lines[2]) == 21:
        m += f"| {message_output_lines[2]}                               |"
    elif len(message_output_lines[2]) == 22:
        m += f"| {message_output_lines[2]}                              |"
    message_output = m

    print(colorama.Fore.YELLOW + " -----------------------------------------------------" + colorama.Style.RESET_ALL)
    print(colorama.Fore.GREEN + message_output + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + " -----------------------------------------------------" + colorama.Style.RESET_ALL)
    print()
    input(colorama.Fore.YELLOW + "[*] enter để quay lại\n-> " + colorama.Style.RESET_ALL)
    return 0



def check_sdt_saved():
    with open("./cloudsigma_sms/phone_saved.txt", "r") as file:
        ds_sdt = file.read().splitlines()
    print()
    print(colorama.Fore.YELLOW + "danh sách số điện thoại bên dưới ↓" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + " ---------------" + colorama.Style.RESET_ALL)
    for sdt in ds_sdt:
        if len(sdt) == 13:
            print(colorama.Fore.YELLOW + f"| {sdt} |" + colorama.Style.RESET_ALL)
        else:
            print(colorama.Fore.YELLOW + f"| {sdt}  |" + colorama.Style.RESET_ALL)
    print(colorama.Fore.YELLOW + " ---------------" + colorama.Style.RESET_ALL)
    input(colorama.Fore.YELLOW + "[*] enter để quay lại\n->" + colorama.Style.RESET_ALL)
    return 0



def delete_hist_phone_number():
    try:
        with open("./cloudsigma_sms/phone_saved.txt", "w") as file:
            file.write("")
        with open("./cloudsigma_sms/phone_saved.txt", "r") as file:
            ds_sdt = file.read().splitlines()
        print(colorama.Fore.YELLOW + "đã làm sạch thành công, xem lại danh sách số điện thoại bên dưới ↓" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + " ---------------" + colorama.Style.RESET_ALL)
        for sdt in ds_sdt:
            if len(sdt) == 13:
                print(colorama.Fore.YELLOW + f"| {sdt} |" + colorama.Style.RESET_ALL)
            else:
                print(colorama.Fore.YELLOW + f"| {sdt}  |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + " ---------------" + colorama.Style.RESET_ALL)
        input(colorama.Fore.YELLOW + "[*] enter để quay lại\n->" + colorama.Style.RESET_ALL)
        return 0
    except Exception as e:
        print(colorama.Fore.RED + f"đã có lỗi không xác định khi làm sạch sdt lưu trữ, mã lỗi: {e}" + colorama.Style.RESET_ALL)
        return 0


def __UI():
    count = 0
    while True:
        if count > 0:
            print()
        print(colorama.Fore.YELLOW + " ---------------------------------------" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| SMSONL TOOL FOR CLOUDSIGMA BY PHUTECH |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| facebook -> Programing Sama           |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| youtube -> Phu Tech                   |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| github -> @phucoding286               |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "|---------------------------------------|" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| 1. chạy tool smsonl để tìm sdt        |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| 2. chạy tool lắng nghe tin nhắn       |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| 3. xem danh sách sdt khả dụng         |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + "| 4. làm sạch danh sách sdt đã lưu      |" + colorama.Style.RESET_ALL)
        print(colorama.Fore.YELLOW + " ---------------------------------------" + colorama.Style.RESET_ALL)
        print()

        choose_input = input(colorama.Fore.YELLOW + "nhập vào lựa chọn của bạn\n-> " + colorama.Style.RESET_ALL)
        if choose_input == "1":
            find_valid_phone()
        elif choose_input == "2":
            listen_cloudsigma_message()
        elif choose_input == "3":
            check_sdt_saved()
        elif choose_input == "4":
            delete_hist_phone_number()
        else:
            print(colorama.Fore.RED + "[!] vui lòng nhập đúng thứ tự" + colorama.Style.RESET_ALL)

        count += 1



if __name__ == "__main__":
    __UI()