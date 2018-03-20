#!/usr/bin/env python3
# Copyright (C) 2017  Ghent University
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from subprocess import run, CalledProcessError, PIPE, STDOUT
from charmhelpers.core.hookenv import (
    status_set,
    log, config,
    is_leader,
) 
from charms.reactive import (
    when,
    when_not,
    set_flag,
    clear_flag,
    endpoint_from_flag,
)

conf = config()
KAFKA_BIN_PATH = "/usr/lib/kafka/bin"

@when_not('config.set.topic-name')
def block_for_topic_name():
    status_set('blocked', 'Waiting for topic-name config.')


@when_not('config.set.partitions')
def block_for_partitions():
    status_set('blocked', 'Waiting for partitions config.')


@when_not('config.set.replication')
def block_for_replication():
    status_set('blocked', 'Waiting for replication config.')


@when('config.set.topic-name',
      'config.set.partitions',
      'config.set.replication',
      'kafka.ready')
@when_not('kafka-topic.created')
def install_kafka_topic():
    if not is_leader():
        return
    kafka = endpoint_from_flag('kafka.ready')
    zookeepers = []
    for zookeeper in kafka.zookeepers():
        zookeepers.append(zookeeper['host'] + ":" + zookeeper['port'])

    topic_exists = check_topic_exists(conf.get('topic-name'), zookeepers)
    if topic_exists is None:
        return
    if not topic_exists:
        status_set('blocked', 'Topic already exists')

    topics_script_path = KAFKA_BIN_PATH + '/kafka-topics.sh'
    try:
        cmd = [topics_script_path,
             "--zookeeper",
             ",".join(zookeepers),
             "--create",
             "--topic",
             conf.get('topic-name'),
             "--partitions",
             str(conf.get('partitions')),
             "--replication-factor",
             str(conf.get('replication')),
        ]
        if conf.get('compact'):
            cmd.extend(['--config', 'cleanup.policy=compact'])

        output = run(cmd, stdout=PIPE, stderr=STDOUT)
        output.check_returncode()
    except CalledProcessError as e:
        log(e)
        status_set('blocked', e.output)
        return
    status_set('active', 'ready ({})'.format(conf.get('topic-name')))
    set_flag('kafka-topic.created')


@when('kafka-topic.created',
      'endpoint.kafka-topic-status.available')
def set_kafka_topic_status():
    if not is_leader():
        return
    topic_status = endpoint_from_flag('endpoint.kafka-topic-status.available')
    topic_status.publish_topic_info(
        {
            'name': conf.get('topic-name'),
            'partitions': conf.get('partitions'),
            'replication': conf.get('replication'),
            'compact': conf.get('compact'),
        }
    )


def check_topic_exists(topic_name, zookeepers):
    try:
        cmd = [
            KAFKA_BIN_PATH + '/kafka-topics.sh',
            '--zookeeper',
            ','.join(zookeepers),
            '--list'
        ]
        output = run(cmd, stdout=PIPE, stderr=STDOUT)
        output.check_returncode()

        topics = output.stdout.decode('utf-8').rstrip().split('\n')
        return True if topic_name in topics else False
    except CalledProcessError as e:
        log(e)
        status_set('blocked', e.output)
        return None
