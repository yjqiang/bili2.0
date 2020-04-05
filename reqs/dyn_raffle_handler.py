class DynRaffleHandlerReq:
    # 特殊的dyn，发图才会出现doc_id
    @staticmethod
    async def create_dyn(user):
        url = 'https://api.vc.bilibili.com/link_draw/v1/doc/create'
        data = {
            'category': 3,
            'type': 0,
            'pictures[0][img_src]': 'http://i0.hdslb.com/bfs/album/419c0c97ac760ca939ac33cc5d90cc5881942ce1.png',
            'pictures[0][img_width]': 600,
            'pictures[0][img_height]': 600,
            'pictures[0][img_size]': 218.75390625,
            'title': '',
            'tags': '',
            'description': '123',
            'setting[copy_forbidden]': 0,
            'setting[cachedTime]': 0,
            'at_uids': '',
            'at_control': [],
            'csrf_token': user.dict_bili['csrf'],
        }

        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def repost_dyn(user, orig_dynid, content, at_uids, ctrl):
        url = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/repost'
        data = {
            'uid': {user.dict_bili['uid']},
            'dynamic_id': int(orig_dynid),
            'content': content,
            'at_uids': at_uids,
            'ctrl': ctrl,
            'csrf_token': user.dict_bili['csrf'],
        }
        json_rsp = await user.other_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=data)
        return json_rsp

    @staticmethod
    async def fetch_dyns(user, uid, offset):
        url = f'https://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history?host_uid={uid}&offset_dynamic_id={offset}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp

    @staticmethod
    async def del_dyn_by_docid(user, doc_id):
        url = f'https://api.vc.bilibili.com/link_draw/v1/doc/delete'
        data = {
            'doc_id': doc_id,
            'csrf_token': user.dict_bili['csrf'],
            'csrf': ''
        }
        json_rsp = await user.other_session.request_json('POST', url, data=data, headers=user.dict_bili['pcheaders'])
        return json_rsp

    @staticmethod
    async def del_dyn_by_dynid(user, dyn_id):
        url = 'https://api.vc.bilibili.com/dynamic_repost/v1/dynamic_repost/rm_rp_dyn'
        payload = {
            'uid': user.dict_bili['uid'],
            'dynamic_id': dyn_id,
            'csrf_token': user.dict_bili['csrf'],
        }

        json_rsp = await user.other_session.request_json('POST', url, headers=user.dict_bili['pcheaders'], data=payload)
        return json_rsp

    @staticmethod
    async def check_dyn_detail(user, doc_id):
        url = f'https://api.vc.bilibili.com/link_draw/v1/doc/detail?doc_id={doc_id}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp

    @staticmethod
    async def fetch_dyn_raffle(user, doc_id):
        url = f'https://api.vc.bilibili.com/lottery_svr/v1/lottery_svr/lottery_notice?business_type=2&business_id={doc_id}'
        json_rsp = await user.other_session.request_json('GET', url)
        return json_rsp
