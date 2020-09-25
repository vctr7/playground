import requests

url = 'http://localhost:8000'
chksum = 0


class Elevator(object):
    def __init__(self, e_id, current_floor, passengers, status):
        self.id = e_id
        self.current_floor = current_floor
        self.passengers = passengers
        self.status = status


def startAPI(URL):
    # ''' start / u_id / problem no. / # of elevator '''
    uri = URL + '/' + 'start' + '/' + 'user_id' + '/' + '2' + '/' + '1'
    return requests.post(uri)


def oncallsAPI(URL, Header):
    uri = URL + '/oncalls'
    return requests.get(uri, headers=Header)


def actionAPI(URL, Header, Commands):
    uri = URL + '/action'
    return requests.post(uri, headers=Header, json={"commands": Commands})


def getCalllist(json):
    return json["calls"]


def getElevlist(json):
    return [Elevator(elev["id"], elev["floor"], elev["passengers"], elev["status"])
            for elev in json["elevators"]]


def decide(call_list, elev_list):
    global chksum
    in_, out_ = {}, {}
    command = []
    destination = 0
    dd = []
    tt = []
    elev = elev_list[0]
    for call in call_list:
        dd.append(call["start"])
        if call["start"] not in in_:
            in_[call["start"]] = [call]
        else:
            in_[call["start"]].append(call)

    for p in elev.passengers:
        tt.append(p["end"])
        if p["end"] not in out_:
            out_[p["end"]] = [p]
        else:
            out_[p["end"]].append(p)

    if not elev.passengers and call_list:
        destination = max(dd)
    if elev.passengers:
        destination = max(tt)
    if destination == 0:
        print("destination err!")
        return None

    if elev.current_floor in out_:
        if elev.status == "UPWARD" or elev.status == "DOWNWARD":
            command.append({"elevator_id": elev.id, "command": "STOP"})
            return command

        elif elev.status == "STOPPED":
            command.append({"elevator_id": elev.id, "command": "OPEN"})
            return command

        elif elev.status == "OPENED":
            counterpart = [c["id"] for c in out_[elev.current_floor]]
            command.append({"elevator_id": elev.id, "command": "EXIT", "call_ids": counterpart})
            return command
            # //// 우선 내릴 사람 다 내리고 다음으로 탈 사람 있는지 확인. 그리고 닫음 ////



    # 해당 층에 탈 사람있는 경우 ( 내릴 사람은 이미 다 내림 )
    if elev.current_floor not in out_ and elev.current_floor in in_ and len(elev.passengers) < 8 and chksum==0:
        if elev.status == "UPWARD" or elev.status == "DOWNWARD":
            command.append({"elevator_id": elev.id, "command": "STOP"})
            return command

        elif elev.status == "STOPPED":
            command.append({"elevator_id": elev.id, "command": "OPEN"})
            return command

        elif elev.status == "OPENED":
            elev_direction = "+" if destination > elev.current_floor else "-"

            if destination == elev.current_floor:
                plus, minus = 0, 0
                for call in in_[elev.current_floor]:
                    if call["start"] > call ["end"]:
                        minus += 1

                    elif call["start"] < call["end"]:
                        plus += 1

                elev_direction = "+" if plus >= minus else "-"

            candidate = []
            # 엘레베이터 진행방향과 같은 것만 태움
            for call in in_[elev.current_floor]:
                if len(candidate) + len(elev.passengers) == 8:
                    break
                if call["start"] > call["end"] and elev_direction == '-':
                    candidate.append(call["id"])
                elif call["start"] < call["end"] and elev_direction == '+':
                    candidate.append(call["id"])

            if candidate:
                command.append({"elevator_id": elev.id, "command": "ENTER", "call_ids": candidate})
                return command
            else:
                command.append({"elevator_id": elev.id, "command": "CLOSE"})
                chksum = 1
                return command
                # //// CLOSING ////
    elif elev.current_floor not in out_ and elev.current_floor not in in_  and len(elev.passengers) < 8 and elev.status == "OPENED":
        command.append({"elevator_id": elev.id, "command": "CLOSE"})
        return command

    if len(elev.passengers) == 8:
        if elev.status=="OPENED":
            command.append({"elevator_id": elev.id, "command": "CLOSE"})
            return command

    if elev.current_floor < destination:
        if elev.status == "STOPPED" or elev.status == "UPWARD":
            chksum=0
            command.append({"elevator_id": elev.id, "command": "UP"})
            return command

    elif elev.current_floor > destination:
        if elev.status == "STOPPED" or elev.status == "DOWNWARD":
            chksum=0
            command.append({"elevator_id": elev.id, "command": "DOWN"})
            return command


# 문제 시작. start로 POST함으로 시작 (user_key / 문제번호 / 엘리베이터 대수 )
start_ret = startAPI(URL=url)
strat_ret_json = start_ret.json()
p_in = {}
p_out = {}
if start_ret.status_code != 200:
    print("Cannot Start the connection due to : ", start_ret.status_code)

else:
    print("Start the connection successfully!")
    token = strat_ret_json['token']
    header = {'X-Auth-Token': token}

    while 1:
        commands = []
        oncalls_ret = oncallsAPI(URL=url, Header=header)
        if oncalls_ret.status_code != 200:
            print("oncallsAPI Fail due to : ", oncalls_ret.status_code)
            break

        oncalls_ret_json = oncalls_ret.json()
        if oncalls_ret_json["is_end"]:
            print("Finish the process!")
            break

        call_list  = oncalls_ret_json["calls"]
        elev_list = getElevlist(oncalls_ret_json)
        command = decide(call_list, elev_list)
        if not command:
            print("command Err")
            break

        action_ret = actionAPI(URL=url, Header=header, Commands=command)
        if action_ret.status_code != 200:
            print("actionAPI Fail due to : ", action_ret.status_code)
            break
