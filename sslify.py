import datetime
import os
import subprocess
import sys
from nginxparser import dumps
from nginxparser import load


# dependency: pip install git+https://github.com/fatiherikli/nginxparser.git
# This is intended to be used as specified in the TWU TechOps Guide at https://thoughtworks.jiveon.com/docs/DOC-22901

def correct_number_args(args):
    if (len(args) not in [4, 5]):
        print "USAGE:", "python sslify.py <term> <team> <env>"
        print "USAGE EXAMPLE:", "python sslify.py 54 5 qa"
        print "USAGE EXAMPLE:", "python sslify.py 54 5 qa redirect_only # only adds https redirect; do this AFTER a second TechOps request"
        return False
    return True


def set_config(args):
    redirect_only = len(args) == 5 and args[4] == "redirect_only"
    return {
        "term": args[1],
        "team": args[2],
        "env": args[3],
        "redirect_only": redirect_only}


def is_server_chunk(server_chunk):
    return server_chunk[1][1][0] == "server_name"


def add_letsencrypt_file_allowance(config, nginx_config):
    for chunk in nginx_config:
        if (is_server_chunk(chunk)):
            server_name = server_name_from(chunk)
            if (matches_env(config, server_name) and matches_team(config, server_name)):
                if (not contains_acme_challenge(chunk)):
                    add_acme_challenge(chunk)
    return nginx_config


def add_https_redirect(config, data):
    for chunk in data:
        if (is_server_chunk(chunk)):
            server_name = server_name_from(chunk)
            if (matches_env(config, server_name) and matches_team(config, server_name)):
                for possible_location_block in chunk[1]:
                    for possible_location_block_subset in possible_location_block:
                        if possible_location_block_subset == ['location', '/']:
                            possible_location_block[1].append(['return', '302 https://$host$request_uri'])
    return data


def add_acme_challenge(chunk):
    chunk[1].append([['location', '/.well-known/acme-challenge/'], [['root', '/var/lib/letsencrypt']]])


def contains_acme_challenge(server_chunk):
    for foo in server_chunk[1]:
        for bar in foo:
            for baz in bar:
                if (baz == '/.well-known/acme-challenge/'):
                    #         do nothing
                    print "Found '/.well-known/acme-challenge/' so we will not add another because nginx doesn't like it"
                    return True
    return False


def server_name_from(server_chunk):
    return server_chunk[1][1][1]


def matches_env(config, server_name):
    env = config["env"]
    if (env == "prod") and (no_other_environments_in(server_name)):
        return True
    return env in server_name


def no_other_environments_in(server_name):
    environments = ["go", "ci", "qa", "staging"]
    for env in environments:
        if env in server_name:
            return False
    return True


def add_ssl_block(config, nginx_conf_data):
    for index in range(len(nginx_conf_data)):
        server_chunk = nginx_conf_data[index]
        if (is_server_name_chunk(server_chunk)):
            server_name = get_server_name(server_chunk)
            if (matches_env(config, server_name) and matches_team(config, server_name)):
                new_block = ssl_block(config, server_name, proxy_pass(server_chunk))
                nginx_conf_data.insert(index + 1, new_block)
                return nginx_conf_data
    return nginx_conf_data


def proxy_pass(server_chunk):
    return server_chunk[1][2][1][2]


def get_server_name(server_chunk):
    server_name = server_chunk[1][1][1]
    return server_name


def is_server_name_chunk(server_chunk):
    return server_chunk[1][1][0] == "server_name"


def ssl_block(config, server_name, proxy_pass):
    environment = env_for_cert_path(config)
    return [['server'],
            [['listen', '443 ssl'],
             ['ssl', 'on'],
             ['ssl_certificate',
              '/home/payment/.acme.sh/' + environment + 'twu' + config["term"] + 'team' + config[
                  "team"] + '.freewheelers.bike/' + environment + 'twu' + config[
                  "term"] + 'team' + config[
                  "team"] + '.freewheelers.bike.cer'],
             ['ssl_certificate_key',
              '/home/payment/.acme.sh/' + environment + 'twu' + config["term"] + 'team' + config[
                  "team"] + '.freewheelers.bike/' + environment + 'twu' + config["term"] + 'team' + config[
                  "team"] + '.freewheelers.bike.key'],
             ['server_name', server_name],
             [['location', '/'],
              [['proxy_set_header', 'X-Real-IP  $remote_addr'],
               ['proxy_set_header', 'Host $host'],
               proxy_pass]]]]


def env_for_cert_path(config):
    if (config["env"] == "prod"):
        environment = ""
    else:
        environment = config["env"] + "-env."
    print "ENVIRONMENT:", environment
    return environment


def matches_team(config, server_name):
    return "team" + config["team"] in server_name


def restart_nginx():
    print "!!!!!!!!! Restarting nginx on freewheelers.bike"
    try:
        prog = subprocess.Popen(["ssh", "freewheelers.bike", "sudo service nginx restart"], stderr=subprocess.PIPE)
        errdata = prog.communicate()[1]
        print errdata
    except:
        print "ERROR: nginx did not restart. Continuing anyway."
        pass


def request_cert(config):
    command = "sudo -u payment -i <<< './acme.sh --issue -d " + env_for_cert_path(config) + "twu" + config["term"] + "team" + config[
        "team"] + ".freewheelers.bike -w /var/lib/letsencrypt'"
    print "COMMAND:", command
    prog = subprocess.Popen(["ssh", "freewheelers.bike", command], stderr=subprocess.PIPE)
    errdata = prog.communicate()[1]
    print errdata


def scp_output_to_server(filename):
    print "Uploading", filename, "to remote server freewheelers.bike/tmp/"
    subprocess.call(["scp", filename, "freewheelers.bike:/tmp/project.conf"])
    print "Done uploading"


def move_remote_tmp_nginx_config_to_real_location():
    print "Copying freewheelers.bike:/tmp/project.conf to freewheelers.bike:/etc/nginx/conf.d/project.conf (with sudo)"
    prog = subprocess.Popen(["ssh", "freewheelers.bike", "sudo cp /tmp/project.conf /etc/nginx/conf.d/project.conf"], stderr=subprocess.PIPE)
    errdata = prog.communicate()[1]
    print errdata
    print "Done copying"


def get_nginx_config_from_freewheelers():
    print "Moving local project.conf if it exists"
    try:
        subprocess.call(["mv", "project.conf", file_date() + "-project.conf"])
    except os.IOError:
        print "No conflicting project.conf file to move"
        pass
    print "Getting remote file:", "freewheelers.bike:/etc/nginx/conf.d/project.conf"
    subprocess.call(["scp", "freewheelers.bike:/etc/nginx/conf.d/project.conf", "."])
    print "Done getting remote file"
    return "project.conf"  # name of file on local filesystem


def file_date():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


def run(args):
    config = set_config(args)

    if (config["redirect_only"]):
        print "Adding the HTTPS redirect line. Hopefully you requested a cert first!"
        get_nginx_config_from_freewheelers()  # remote call
        config_without_redirect = load(open("project.conf"))
        with_redirect = add_https_redirect(config, config_without_redirect)
        file_with_https_redirect = "file_with_https_redirect_project.conf"
        config_to_file(file_with_https_redirect, with_redirect)
        upload_changed_config(file_with_https_redirect)  # remote call
        print "Done adding the HTTPS redirect line. The new config has been uploaded and the nginx server has been restarted."
        return

    get_nginx_config_from_freewheelers()  # remote call

    nginx_config = load(open("project.conf"))
    nginx_config_with_known_block = add_letsencrypt_file_allowance(config, nginx_config)
    first_out_file = "out1.conf"
    print "writing modified nginx config to:", first_out_file
    config_to_file(first_out_file, nginx_config_with_known_block)

    upload_changed_config(first_out_file)  # remote call
    request_cert(config)  # remote call

    nginx_config_after_first_write = load(open(first_out_file))
    nginx_config_with_ssl_block = add_ssl_block(config, nginx_config_after_first_write)
    second_out_file = "out2.conf"
    print "writing nginx config with ssl block to:", second_out_file
    config_to_file(second_out_file, nginx_config_with_ssl_block)

    upload_changed_config(second_out_file)  # remote call


def config_to_file(filename, data):
    text_file = open(filename, "w")
    text_file.write(dumps(data))
    text_file.close()


def upload_changed_config(filename):
    scp_output_to_server(filename)  # remote call
    move_remote_tmp_nginx_config_to_real_location()  # remote call
    restart_nginx()  # remote call


if __name__ == "__main__":
    args = sys.argv
    if correct_number_args(args):
        run(args)
