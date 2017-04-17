import nginxparser
from flexmock import flexmock

import sslify


class TestSslify:
    def test_run(self):
        # Note: this is a top-level integration tests and writes to the filesystem
        flexmock(sslify).should_receive('get_nginx_config_from_freewheelers')
        open('project.conf', 'w').write(open("test_data_twu54team1qa.config", 'r').read())  # create a fake local file

        flexmock(sslify).should_receive('scp_output_to_server')
        flexmock(sslify).should_receive('move_remote_tmp_nginx_config_to_real_location')
        flexmock(sslify).should_receive('restart_nginx')
        flexmock(sslify).should_receive('request_cert')
        flexmock(sslify).should_receive('scp_output_to_server')
        flexmock(sslify).should_receive('move_remote_tmp_nginx_config_to_real_location')
        flexmock(sslify).should_receive('restart_nginx')

        sslify.run(self.good_args_54_1_qa())

        file_with_final_results = "out2.conf"
        amended_data = nginxparser.load(open(file_with_final_results))
        assert amended_data != nginxparser.load(open("test_data_twu54team1qa.config", 'r'))
        assert nginxparser.load(open(file_with_final_results)) == self.expected_full_amended_data()

    def test_add_https_redirect(self):
        existing_config = nginxparser.load(open("test_data_twu54team1qa_with_known_host.config"))
        with_https_redirect = sslify.add_https_redirect(self.qa_team1_term54_config(), existing_config)
        expected = nginxparser.load(open("test_data_twu54team1qa_with_known_host_and_redirect.config"))
        assert with_https_redirect == expected

    def qa_team1_term54_config(self):
        config = {'env': 'qa', 'team': '1', 'term': '54'}
        return config

    def test_do_not_add_ssl_block_for_wrong_environment(self):
        config = {'env': 'staging', 'team': '1', 'term': '54'}
        result = sslify.add_ssl_block(config, self.load_term54team5envqa_with_known_host())
        assert result == self.load_term54team5envqa_with_known_host()

    def test_add_ssl_block_for_prod_which_behaves_differently(self):
        config = {'env': 'prod', 'team': '1', 'term': '54'}
        result = sslify.add_ssl_block(config, self.load_term54team5env_prod())
        assert result != self.load_term54team5env_prod()
        assert result == self.project_conf_with_prod_https_block()

    def load_term54team5env_prod(self):
        return nginxparser.load(open("test_data_twu54team1prod_with_known_host.config"))

    def test_add_ssl_block(self):
        result = sslify.add_ssl_block(self.qa_team1_term54_config(), self.load_term54team5envqa_with_known_host())
        assert result != self.load_term54team5envqa_with_known_host()
        assert result == self.project_conf_with_ssl_block()

    def load_term54team5envqa_with_known_host(self):
        return nginxparser.load(open("test_data_twu54team1qa_with_known_host.config"))

    def test_matches_env_CI(self):
        server_name = '~^(www\\.)?ci-env\\.twu54team1\\.freewheelers\\.bike$'
        config = {'env': 'ci', 'team': '1', 'term': '54'}
        assert True == sslify.matches_env(config, server_name)

        wrong_config = self.qa_team1_term54_config()
        assert False == sslify.matches_env(wrong_config, server_name)

    def test_matches_env_QA(self):
        server_name = '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'
        assert True == sslify.matches_env(self.qa_team1_term54_config(), server_name)

        wrong_config = {'env': 'staging', 'team': '1', 'term': '54'}
        assert False == sslify.matches_env(wrong_config, server_name)

    def test_matches_env_Staging(self):
        server_name = '~^(www\\.)?staging-env\\.twu54team1\\.freewheelers\\.bike$'
        config = {'env': 'staging', 'team': '1', 'term': '54'}
        assert True == sslify.matches_env(config, server_name)

        wrong_config = {'env': 'prod', 'team': '1', 'term': '54'}
        assert False == sslify.matches_env(wrong_config, server_name)

    def test_matches_env_Prod(self):
        server_name = '~^(www\.)?twu54team1\.freewheelers\.bike$;'
        config = {'env': 'prod', 'team': '1', 'term': '54'}
        assert True == sslify.matches_env(config, server_name)

        wrong_config = self.qa_team1_term54_config()
        assert False == sslify.matches_env(wrong_config, server_name)

    def good_args_54_1_qa(self):
        term = "54"
        team = "1"
        env = "qa"
        args = ["name_of_file", term, team, env]
        return args

    def good_args_54_1_qa_redirect_only(self):
        return self.good_args_54_1_qa() + ["redirect_only"]

    def load_term54team5envqa(self):
        return nginxparser.load(open("test_data_twu54team1qa.config"))

    def test_correct_number_args_ok(self):
        args_ok = sslify.correct_number_args(self.good_args_54_1_qa())
        assert args_ok == True

    def test_correct_number_args_ok_with_redirect_only_option(self):
        args_ok = sslify.correct_number_args(self.good_args_54_1_qa_redirect_only())
        assert args_ok == True

    def test_correct_number_args_not_ok(self):
        args_ok = sslify.correct_number_args([])
        assert args_ok == False

    def test_set_config(self):
        config = sslify.set_config(self.good_args_54_1_qa())
        assert config == {'env': 'qa', 'team': '1', 'term': '54', 'redirect_only': False}

    def test_set_config_with_redirect_only(self):
        config = sslify.set_config(self.good_args_54_1_qa_redirect_only())
        assert config == {'env': 'qa', 'team': '1', 'term': '54', 'redirect_only': True}

    def test_changes_nothing_if_wrong_term__add_letsencrypt_file_allowance(self):
        original = self.load_term54team5envqa()
        config = {'env': 'qa', 'team': '1', 'term': '99'}
        result = sslify.add_letsencrypt_file_allowance(config, original)
        assert result == original

    def test_changes_nothing_if_wrong_team__test_add_letsencrypt_file_allowance(self):
        original = self.load_term54team5envqa()
        config = {'env': 'qa', 'team': '99', 'term': '54'}
        result = sslify.add_letsencrypt_file_allowance(config, original)
        assert result == original

    def test_changes_nothing_if_wrong_env__test_add_letsencrypt_file_allowance(self):
        original = self.load_term54team5envqa()
        config = {'env': '99', 'team': '1', 'term': '54'}
        result = sslify.add_letsencrypt_file_allowance(config, original)
        assert result == original

    def test_changes_data_if_correct_term_team_env__test_add_letsencrypt_file_allowance(self):
        result = sslify.add_letsencrypt_file_allowance(self.qa_team1_term54_config(), self.load_term54team5envqa())
        assert result != self.load_term54team5envqa()
        print result
        assert result == self.server_block_with_wellknown()

    def test_does_not_add_wellknown_twice__test_add_letsencrypt_file_allowance(self):
        result1 = sslify.add_letsencrypt_file_allowance(self.qa_team1_term54_config(), self.load_term54team5envqa())
        result2 = sslify.add_letsencrypt_file_allowance(self.qa_team1_term54_config(), result1)
        assert result2 != self.load_term54team5envqa()
        assert result2 == result1
        assert result2 == self.server_block_with_wellknown()

    def server_block_with_wellknown(self):
        return [
            [
                ['server'], [
                ['listen', '80'], ['server_name', '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'],
                [
                    ['location', '/'], [
                    ['proxy_set_header', 'X-Real-IP  $remote_addr'], ['proxy_set_header', 'Host $host'],
                    ['proxy_pass', 'http://10.0.3.250:8080']
                ]
                ],
                [
                    ['location', '/.well-known/acme-challenge/'], [
                    ['root', '/var/lib/letsencrypt']
                ]
                ]
            ]
            ]
        ]

    def expected_full_amended_data(self):
        return [
            [['server'], [['listen', '80'], ['server_name', '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'], [['location', '/'],
                                                                                                                       [[
                                                                                                                           'proxy_set_header',
                                                                                                                           'X-Real-IP  $remote_addr'],
                                                                                                                           [
                                                                                                                               'proxy_set_header',
                                                                                                                               'Host $host'],
                                                                                                                           ['proxy_pass',
                                                                                                                            'http://10.0.3.250:8080']]],
                          [['location', '/.well-known/acme-challenge/'], [['root', '/var/lib/letsencrypt']]]]], [['server'],
                                                                                                                 [['listen', '443 ssl'],
                                                                                                                  ['ssl', 'on'],
                                                                                                                  ['ssl_certificate',
                                                                                                                   '/home/payment/.acme.sh/qa-env.twu54team1.freewheelers.bike/qa-env.twu54team1.freewheelers.bike.cer'],
                                                                                                                  ['ssl_certificate_key',
                                                                                                                   '/home/payment/.acme.sh/qa-env.twu54team1.freewheelers.bike/qa-env.twu54team1.freewheelers.bike.key'],
                                                                                                                  ['server_name',
                                                                                                                   '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'],
                                                                                                                  [['location', '/'], [
                                                                                                                      ['proxy_set_header',
                                                                                                                       'X-Real-IP  $remote_addr'],
                                                                                                                      ['proxy_set_header',
                                                                                                                       'Host $host'],
                                                                                                                      ['proxy_pass',
                                                                                                                       'http://10.0.3.250:8080']]]]]]

    def project_conf_with_prod_https_block(self):
        return [[['server'], [['listen', '80'], ['server_name', '~^(www\\.)?twu54team1\\.freewheelers\\.bike$'], [['location', '/'], [
            ['proxy_set_header', 'X-Real-IP  $remote_addr'], ['proxy_set_header', 'Host $host'], ['proxy_pass', 'http://10.4.4.250:8080']]],
                              [['location', '/.well-known/acme-challenge/'], [['root', '/var/lib/letsencrypt']]]]], [['server'],
                                                                                                                     [['listen', '443 ssl'],
                                                                                                                      ['ssl', 'on'],
                                                                                                                      ['ssl_certificate',
                                                                                                                       '/home/payment/.acme.sh/twu54team1.freewheelers.bike/twu54team1.freewheelers.bike.cer'],
                                                                                                                      [
                                                                                                                          'ssl_certificate_key',
                                                                                                                          '/home/payment/.acme.sh/twu54team1.freewheelers.bike/twu54team1.freewheelers.bike.key'],
                                                                                                                      ['server_name',
                                                                                                                       '~^(www\\.)?twu54team1\\.freewheelers\\.bike$'],
                                                                                                                      [['location', '/'], [[
                                                                                                                          'proxy_set_header',
                                                                                                                          'X-Real-IP  $remote_addr'],
                                                                                                                          [
                                                                                                                              'proxy_set_header',
                                                                                                                              'Host $host'],
                                                                                                                          [
                                                                                                                              'proxy_pass',
                                                                                                                              'http://10.4.4.250:8080']]]]]]

    def project_conf_with_ssl_block(self):
        return [
            [
                ['server'],
                [
                    ['listen', '80'],
                    ['server_name', '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'],
                    [
                        ['location', '/'],
                        [
                            ['proxy_set_header', 'X-Real-IP  $remote_addr'],
                            ['proxy_set_header', 'Host $host'],
                            ['proxy_pass', 'http://10.4.4.250:8080']
                        ]
                    ],
                    [
                        ['location', '/.well-known/acme-challenge/'],
                        [
                            ['root', '/var/lib/letsencrypt']
                        ]
                    ]
                ]
            ],
            [
                ['server'],
                [
                    ['listen', '443 ssl'],
                    ['ssl', 'on'],
                    ['ssl_certificate',
                     '/home/payment/.acme.sh/qa-env.twu54team1.freewheelers.bike/qa-env.twu54team1.freewheelers.bike.cer'],
                    ['ssl_certificate_key', '/home/payment/.acme.sh/qa-env.twu54team1.freewheelers.bike/qa-env.twu54team1.freewheelers.bike.key'],
                    ['server_name', '~^(www\\.)?qa-env\\.twu54team1\\.freewheelers\\.bike$'],
                    [
                        ['location', '/'],
                        [
                            ['proxy_set_header', 'X-Real-IP  $remote_addr'],
                            ['proxy_set_header', 'Host $host'],
                            ['proxy_pass', 'http://10.4.4.250:8080']
                        ]
                    ]
                ]
            ]
        ]
