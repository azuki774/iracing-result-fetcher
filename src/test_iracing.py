import iracing


def test_a_href_list_to_subsession_id():
    tt = [
        {
            "name": "normal",
            "args": [
                "javascript:void(0);",
                "https://forums.iracing.com",
                "javascript:launchEventResult(77777777,99999999);",  # extracted
                "/membersite/member/CareerStats.do?custid=99999999",
                "javascript:launchEventResult(88888888,99999999);",  # extracted
            ],
            "want": [
                "77777777",
                "88888888",
            ],
        }
    ]

    for t in tt:
        assert t["want"] == iracing.a_href_list_to_subsession_id(t["args"])
