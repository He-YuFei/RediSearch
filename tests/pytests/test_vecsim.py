# -*- coding: utf-8 -*-
import base64
import random
import string
import unittest
from time import sleep

import numpy as np
from RLTest import Env

from common import *
from includes import *


def test_sanity(env):
    conn = getConnectionByEnv(env)
    vecsim_type = ['FLAT', 'HNSW']
    for vs_type in vecsim_type:
        conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', vs_type, '6', 'TYPE', 'FLOAT32', 'DIM', '2','DISTANCE_METRIC', 'L2')
        conn.execute_command('HSET', 'a', 'v', 'aaaaaaaa')
        conn.execute_command('HSET', 'b', 'v', 'aaaabaaa')
        conn.execute_command('HSET', 'c', 'v', 'aaaaabaa')
        conn.execute_command('HSET', 'd', 'v', 'aaaaaaba')

        res = [4L, 'a', ['score', '0', 'v', 'aaaaaaaa'],
                   'b', ['score', '3.09485009821e+26', 'v', 'aaaabaaa'],
                   'c', ['score', '2.02824096037e+31', 'v', 'aaaaabaa'],
                   'd', ['score', '1.32922799578e+36', 'v', 'aaaaaaba']]
        res1 = conn.execute_command('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $blob AS score]', 'PARAMS', '2', 'blob', 'aaaaaaaa', 'SORTBY', 'score', 'ASC')
        env.assertEqual(res, res1)

        # todo: make test work on coordinator
        res = [4L, 'c', ['score', '0', 'v', 'aaaaabaa'],
                   'b', ['score', '2.01242627636e+31', 'v', 'aaaabaaa'],
                   'a', ['score', '2.02824096037e+31', 'v', 'aaaaaaaa'],
                   'd', ['score', '1.31886368448e+36', 'v', 'aaaaaaba']]
        res1 = conn.execute_command('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $blob AS score]', 'PARAMS', '2', 'blob', 'aaaaabaa', 'SORTBY', 'score', 'ASC')
        env.assertEqual(res, res1)

        expected_res = ['__v_score', '0', 'v', 'aaaaaaaa']
        res = conn.execute_command('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $blob]', 'PARAMS', '2', 'blob', 'aaaaaaaa', 'SORTBY', '__v_score', 'ASC', 'LIMIT', 0, 1)
        env.assertEqual(res[2], expected_res)

        #####################
        ## another example ##
        #####################
        message = 'aaaaabaa'
        res = conn.execute_command('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b]', 'PARAMS', '2', 'b', message, 'SORTBY', '__v_score', 'ASC', 'LIMIT', 0, 1)
        env.assertEqual(res[2], ['__v_score', '0', 'v', 'aaaaabaa'])

        conn.execute_command('FT.DROPINDEX', 'idx', 'DD')

def testEscape(env):
    return
    conn = getConnectionByEnv(env)

    vecsim_type = ['FLAT', 'HNSW']
    for vs_type in vecsim_type:
        conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', vs_type, '6', 'TYPE', 'FLOAT32', 'DIM', '2','DISTANCE_METRIC', 'L2')
        conn.execute_command('HSET', 'a', 'v', '////////')
        conn.execute_command('HSET', 'b', 'v', '++++++++')
        conn.execute_command('HSET', 'c', 'v', 'abcdefgh')
        conn.execute_command('HSET', 'd', 'v', 'aacdefgh')
        conn.execute_command('HSET', 'e', 'v', 'aaadefgh')

        messages = ['\+\+\+\+\+\+\+\+', '\/\/\/\/\/\/\/\/', 'abcdefgh', 'aacdefgh', 'aaadefgh']
        for message in messages:
            res = conn.execute_command('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b AS score]', 'PARAMS', '2', 'b', message, 'SORTBY', 'score', 'ASC', 'LIMIT', 0, 1)
            env.assertEqual(res[2][3], message.replace('\\', ''))

        conn.execute_command('FT.DROPINDEX', 'idx', 'DD')

def testDel(env):
    conn = getConnectionByEnv(env)
    vecsim_type = ['FLAT', 'HNSW']
    for vs_type in vecsim_type:
        conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', vs_type, '6', 'TYPE', 'FLOAT32', 'DIM', '2','DISTANCE_METRIC', 'L2')

        conn.execute_command('HSET', 'a', 'v', 'aaaaaaaa')
        conn.execute_command('HSET', 'b', 'v', 'aaaaaaba')
        conn.execute_command('HSET', 'c', 'v', 'aaaabaaa')
        conn.execute_command('HSET', 'd', 'v', 'aaaaabaa')

        expected_res = ['a', ['score', '0', 'v', 'aaaaaaaa'], 'c', ['score', '3.09485009821e+26', 'v', 'aaaabaaa'],
                        'd', ['score', '2.02824096037e+31', 'v', 'aaaaabaa'], 'b', ['score', '1.32922799578e+36', 'v', 'aaaaaaba']]

        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b AS score]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', 'score', 'ASC', 'LIMIT', 0, 1)
        env.assertEqual(res[1:3], expected_res[0:2])
        
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b AS score]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', 'score', 'ASC', 'LIMIT', 0, 2)
        env.assertEqual(res[1:5], expected_res[0:4])
        
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 3 @v $b AS score]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', 'score', 'ASC', 'LIMIT', 0, 3)
        env.assertEqual(res[1:7], expected_res[0:6])
        
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b AS score]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', 'score', 'ASC', 'LIMIT', 0, 4)
        env.assertEqual(res[1:9], expected_res[0:8])
        
        conn.execute_command('DEL', 'a')
        
        expected_res = ['c', ['__v_score', '3.09485009821e+26', 'v', 'aaaabaaa'],
                        'd', ['__v_score', '2.02824096037e+31', 'v', 'aaaaabaa'],
                        'b', ['__v_score', '1.32922799578e+36', 'v', 'aaaaaaba']]
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', '__v_score', 'ASC', 'LIMIT', 0, 1)
        env.assertEqual(res[1:3], expected_res[:2])
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', '__v_score', 'ASC', 'LIMIT', 0, 2)
        env.assertEqual(res[1:5], expected_res[:4])
        res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 3 @v $b]', 'PARAMS', '2', 'b', 'aaaaaaaa', 'SORTBY', '__v_score', 'ASC', 'LIMIT', 0, 3)
        env.assertEqual(res[1:7], expected_res[:6])

        # '''
        # This test returns 4 results instead of the expected 3. The HNSW library return the additional results.
        env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh', 'RETURN', '1', 'v').equal([3L, 'b', ['v', 'aaaaaaba'], 'c', ['v', 'aaaabaaa'], 'd', ['v', 'aaaaabaa']])
        # '''

        conn.execute_command('FT.DROPINDEX', 'idx', 'DD')


def testDelReuse(env):

    def test_query_empty(env):
        conn = getConnectionByEnv(env)
        vecsim_type = ['FLAT', 'HNSW']
        for vs_type in vecsim_type:
            conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', vs_type, '6', 'TYPE', 'FLOAT32', 'DIM', '2','DISTANCE_METRIC', 'L2')
            env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').equal([0L])
            conn.execute_command('HSET', 'a', 'v', 'redislab')
            env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').equal([1L, 'a', ['v', 'redislab']])
            conn.execute_command('DEL', 'a')
            env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 1 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').equal([0L])
            conn.execute_command('FT.DROPINDEX', 'idx', 'DD')

    def del_insert(env):
        conn = getConnectionByEnv(env)

        conn.execute_command('DEL', 'a')
        conn.execute_command('DEL', 'b')
        conn.execute_command('DEL', 'c')
        conn.execute_command('DEL', 'd')

        env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').equal([0L])

        res = [''.join(random.choice(string.lowercase) for x in range(8)),
            ''.join(random.choice(string.lowercase) for x in range(8)),
            ''.join(random.choice(string.lowercase) for x in range(8)),
            ''.join(random.choice(string.lowercase) for x in range(8))]

        conn.execute_command('HSET', 'a', 'v', res[0])
        conn.execute_command('HSET', 'b', 'v', res[1])
        conn.execute_command('HSET', 'c', 'v', res[2])
        conn.execute_command('HSET', 'd', 'v', res[3])
        return res

    # test start
    conn = getConnectionByEnv(env)
    conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', '2','DISTANCE_METRIC', 'L2')

    vecs = del_insert(env)
    res = [4L, 'a', ['v', vecs[0]], 'b', ['v', vecs[1]], 'c', ['v', vecs[2]], 'd', ['v', vecs[3]]]
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh', 'RETURN', '1', 'v').equal(res)

    vecs = del_insert(env)
    res = [4L, 'a', ['v', vecs[0]], 'b', ['v', vecs[1]], 'c', ['v', vecs[2]], 'd', ['v', vecs[3]]]
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh', 'RETURN', '1', 'v').equal(res)

    vecs = del_insert(env)
    res = [4L, 'a', ['v', vecs[0]], 'b', ['v', vecs[1]], 'c', ['v', vecs[2]], 'd', ['v', vecs[3]]]
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh', 'RETURN', '1', 'v').equal(res)

def load_vectors_to_redis(env, n_vec, query_vec_index, vec_size):
    conn = getConnectionByEnv(env)
    for i in range(n_vec):
        vector = np.random.rand(1, vec_size).astype(np.float32)
        if i == query_vec_index:
            query_vec = vector
        conn.execute_command('HSET', i, 'vector', vector.tobytes())
    return query_vec

def query_vector(env, idx, query_vec):
    conn = getConnectionByEnv(env)
    return conn.execute_command('FT.SEARCH', idx, '*=>[TOP_K 5 @vector $v AS score]', 'PARAMS', '2', 'v', query_vec.tobytes(),
                                'SORTBY', 'score', 'ASC', 'RETURN', 1, 'score', 'LIMIT', 0, 5)

def testDelReuseLarge(env):
    conn = getConnectionByEnv(env)
    INDEX_NAME = 'items'
    prefix = 'item'
    n_vec = 5
    query_vec_index = 3
    vec_size = 1280

    conn.execute_command('FT.CREATE', INDEX_NAME, 'ON', 'HASH',
                         'SCHEMA', 'vector', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', '1280', 'DISTANCE_METRIC', 'L2')
    for _ in range(3):
        query_vec = load_vectors_to_redis(env, n_vec, query_vec_index, vec_size)
        res = query_vector(env, INDEX_NAME, query_vec)
        for i in range(4):
            env.assertLessEqual(float(res[2 + i * 2][1]), float(res[2 + (i + 1) * 2][1]))

def testCreate(env):
    env.skipOnCluster()
    conn = getConnectionByEnv(env)
    conn.execute_command('FT.CREATE', 'idx1', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '14', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '10', 'M', '16', 'EF_CONSTRUCTION', '200', 'EF_RUNTIME', '10')
    for _ in env.retry_with_rdb_reload():
        info = [['identifier', 'v', 'attribute', 'v', 'type', 'VECTOR']]
        assertInfoField(env, 'idx1', 'attributes', info)
        env.assertEqual(env.cmd("FT.DEBUG", "VECSIM_INFO", "idx1", "v")[:-1], ['ALGORITHM', 'HNSW', 'TYPE', 'FLOAT32', 'DIMENSION', 1024L, 'METRIC', 'IP', 'INDEX_SIZE', 0L, 'M', 16L, 'EF_CONSTRUCTION', 200L, 'EF_RUNTIME', 10L, 'MAX_LEVEL', -1L, 'ENTRYPOINT', -1L, 'MEMORY'])

    # Uncomment these tests when support for FLOAT64, INT32, INT64, is added.
    # Trying to run these tests right now will cause 'Bad arguments for vector similarity HNSW index type' error

    # conn.execute_command('FT.CREATE', 'idx2', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '14', 'TYPE', 'FLOAT64', 'DIM', '4096', 'DISTANCE_METRIC', 'L2', 'INITIAL_CAP', '10', 'M', '32', 'EF_CONSTRUCTION', '100', 'EF_RUNTIME', '20')
    # info = [['identifier', 'v', 'attribute', 'v', 'type', 'VECTOR', 'ALGORITHM', 'HNSW', 'TYPE', 'FLOAT64', 'DIM', '4096', 'DISTANCE_METRIC', 'L2', 'M', '32', 'EF_CONSTRUCTION', '100', 'EF_RUNTIME', '20']]
    # assertInfoField(env, 'idx2', 'attributes', info)

    # conn.execute_command('FT.CREATE', 'idx3', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '14', 'TYPE', 'INT32', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE', 'INITIAL_CAP', '10', 'M', '64', 'EF_CONSTRUCTION', '400', 'EF_RUNTIME', '50')
    # info = [['identifier', 'v', 'attribute', 'v', 'type', 'VECTOR', 'ALGORITHM', 'HNSW', 'TYPE', 'INT32', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE', 'M', '64', 'EF_CONSTRUCTION', '400', 'EF_RUNTIME', '50']]
    # assertInfoField(env, 'idx3', 'attributes', info)

    # conn.execute_command('FT.CREATE', 'idx4', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'INT64', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE')
    # info = [['identifier', 'v', 'attribute', 'v', 'type', 'VECTOR', 'ALGORITHM', 'HNSW', 'TYPE', 'INT64', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE', 'M', '16', 'EF_CONSTRUCTION', '200', 'EF_RUNTIME', '10']]
    # assertInfoField(env, 'idx4', 'attributes', info)

    # conn.execute_command('FT.CREATE', 'idx5', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '6', 'TYPE', 'INT32', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE')
    # info = [['identifier', 'v', 'attribute', 'v', 'type', 'VECTOR', 'ALGORITHM', 'FLAT', 'TYPE', 'INT32', 'DIM', '64', 'DISTANCE_METRIC', 'COSINE', 'BLOCK_SIZE', str(1024 * 1024)]]
    # assertInfoField(env, 'idx5', 'attributes', info)

def testCreateErrors(env):
    env.skipOnCluster()
    conn = getConnectionByEnv(env)
    # missing init args
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR').error().contains('Bad arguments for vector similarity algorithm')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT').error().contains('Bad arguments for vector similarity number of parameters')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '6').error().contains('Expected 6 parameters but got 0')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '1').error().contains('Bad number of arguments for vector similarity index: got 1 but expected even number')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '2', 'SIZE').error().contains('Bad arguments for algorithm FLAT: SIZE')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '2', 'TYPE').error().contains('Bad arguments for vector similarity FLAT index type')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '4', 'TYPE', 'FLOAT32', 'DIM').error().contains('Bad arguments for vector similarity FLAT index dim')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '4', 'DIM', '1024', 'DISTANCE_METRIC', 'IP').error().contains('Missing mandatory parameter: cannot create FLAT index without specifying TYPE argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '4', 'TYPE', 'FLOAT32', 'DISTANCE_METRIC', 'IP').error().contains('Missing mandatory parameter: cannot create FLAT index without specifying DIM argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '4', 'TYPE', 'FLOAT32', 'DIM', '1024').error().contains('Missing mandatory parameter: cannot create FLAT index without specifying DISTANCE_METRIC argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '6', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC').error().contains('Bad arguments for vector similarity FLAT index metric')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW').error().contains('Bad arguments for vector similarity number of parameters')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6').error().contains('Expected 6 parameters but got 0')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '1').error().contains('Bad number of arguments for vector similarity index: got 1 but expected even number')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '2', 'SIZE').error().contains('Bad arguments for algorithm HNSW: SIZE')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '2', 'TYPE').error().contains('Bad arguments for vector similarity HNSW index type')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '4', 'TYPE', 'FLOAT32', 'DIM').error().contains('Bad arguments for vector similarity HNSW index dim')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '4', 'DIM', '1024', 'DISTANCE_METRIC', 'IP').error().contains('Missing mandatory parameter: cannot create HNSW index without specifying TYPE argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '4', 'TYPE', 'FLOAT32', 'DISTANCE_METRIC', 'IP').error().contains('Missing mandatory parameter: cannot create HNSW index without specifying DIM argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '4', 'TYPE', 'FLOAT32', 'DIM', '1024').error().contains('Missing mandatory parameter: cannot create HNSW index without specifying DISTANCE_METRIC argument')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC').error().contains('Bad arguments for vector similarity HNSW index metric')

    # invalid init args
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'DOUBLE', 'DIM', '1024', 'DISTANCE_METRIC', 'IP').error().contains('Bad arguments for vector similarity HNSW index type')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', 'str', 'DISTANCE_METRIC', 'IP').error().contains('Bad arguments for vector similarity HNSW index dim')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'REDIS').error().contains('Bad arguments for vector similarity HNSW index metric')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'REDIS', '6', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP').error().contains('Bad arguments for vector similarity algorithm')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '10', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', 'str', 'BLOCK_SIZE', '16') \
        .error().contains('Bad arguments for vector similarity FLAT index initial cap')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'FLAT', '10', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '10', 'BLOCK_SIZE', 'str') \
        .error().contains('Bad arguments for vector similarity FLAT index blocksize')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '12', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', 'str', 'M', '16', 'EF_CONSTRUCTION', '200') \
        .error().contains('Bad arguments for vector similarity HNSW index initial cap')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '12', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '100', 'M', 'str', 'EF_CONSTRUCTION', '200') \
        .error().contains('Bad arguments for vector similarity HNSW index m')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '12', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '100', 'M', '16', 'EF_CONSTRUCTION', 'str') \
        .error().contains('Bad arguments for vector similarity HNSW index efConstruction')
    env.expect('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '12', 'TYPE', 'FLOAT32', 'DIM', '1024', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '100', 'M', '16', 'EF_RUNTIME', 'str') \
        .error().contains('Bad arguments for vector similarity HNSW index efRuntime')


def testSearchErrors(env):
    env.skipOnCluster()
    conn = getConnectionByEnv(env)
    conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 's', 'TEXT', 't', 'TAG', 'SORTABLE', 'v', 'VECTOR', 'HNSW', '12', 'TYPE', 'FLOAT32', 'DIM', '2', 'DISTANCE_METRIC', 'IP', 'INITIAL_CAP', '10', 'M', '16', 'EF_CONSTRUCTION', '200')
    conn.execute_command('HSET', 'a', 'v', 'aaaaaaaa')
    conn.execute_command('HSET', 'b', 'v', 'bbbbbbbb')
    conn.execute_command('HSET', 'c', 'v', 'cccccccc')
    conn.execute_command('HSET', 'd', 'v', 'dddddddd')

    env.expect('FT.SEARCH', 'idx', '*=>[REDIS 4 @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Syntax error')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K str @v $b]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Syntax error')

    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b]', 'PARAMS', '2', 'b', 'abcdefg').error().contains('query vector does not match index\'s type or dimention')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b]', 'PARAMS', '2', 'b', 'abcdefghi').error().contains('query vector does not match index\'s type or dimention')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @t $b]', 'PARAMS', '2', 'b', 'abcdefgh').equal([0]) # wrong field
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b AS v]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Property `v` already exists in schema')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b AS s]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Property `s` already exists in schema')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b AS t]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Property `t` already exists in schema')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b AS $score]', 'PARAMS', '4', 'score', 't', 'b', 'abcdefgh').error().contains('Property `t` already exists in schema')

    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b EF_RUNTIME -42]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Error parsing vector similarity parameters: Attribute not supported for term')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b EF_RUNTIME 2.71828]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Error parsing vector similarity parameters: Attribute not supported for term')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b EF_RUNTIME 5 EF_RUNTIME 6]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Error parsing vector similarity parameters: Field was specified twice')
    env.expect('FT.SEARCH', 'idx', '*=>[TOP_K 2 @v $b EF_FUNTIME 30]', 'PARAMS', '2', 'b', 'abcdefgh').error().contains('Error parsing vector similarity parameters: Invalid option')


def load_vectors_into_redis(con, vector_field, dim, num_vectors):
    id_vec_list = []
    p = con.pipeline(transaction=False)
    for i in range(1, num_vectors+1):
        vector = np.float32([i for j in range(dim)])
        con.execute_command('HSET', i, vector_field, vector.tobytes(), 't', 'text value')
        id_vec_list.append((i, vector))
    p.execute()
    return id_vec_list

def test_with_fields(env):
    conn = getConnectionByEnv(env)
    dimension = 128
    qty = 100

    conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32', 'DIM', dimension, 'DISTANCE_METRIC', 'L2', 't', 'TEXT')
    load_vectors_into_redis(conn, 'v', dimension, qty)

    query_data = np.float32(np.random.random((1, dimension)))
    res = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 100 @v $vec_param AS score]',
                    'SORTBY', 'score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
                    'RETURN', 2, 'score', 't')
    res_nocontent = env.cmd('FT.SEARCH', 'idx', '*=>[TOP_K 100 @v $vec_param AS score]',
                    'SORTBY', 'score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
                    'NOCONTENT')
    env.assertEqual(res[1::2], res_nocontent[1:])
    env.assertEqual('t', res[2][2])


def get_vecsim_memory(env, index_key, field_name):
    return float(to_dict(env.cmd("FT.DEBUG", "VECSIM_INFO", index_key, field_name))["MEMORY"])/0x100000


def test_memory_info(env):
    # Skip on cluster as FT.DEBUG not supported.
    env.skipOnCluster()
    # This test flow adds two vectors and deletes them. The test checks for memory increase in Redis and RediSearch upon insertion and decrease upon delete.
    conn = getConnectionByEnv(env)
    dimension = 128
    index_key = 'idx'
    vector_field = 'v'

    # Create index. Flat index implementation will free memory when deleting vectors, so it is a good candidate for this test with respect to memory consumption.
    conn.execute_command('FT.CREATE', index_key, 'SCHEMA', vector_field, 'VECTOR', 'FLAT', '8', 'TYPE', 'FLOAT32', 'DIM', dimension, 'DISTANCE_METRIC', 'L2', 'BLOCK_SiZE', '1')
    # Verify redis memory >= redisearch index memory
    vecsim_memory = get_vecsim_memory(env, index_key=index_key, field_name=vector_field)
    redisearch_memory = get_redisearch_vector_index_memory(env, index_key=index_key)
    redis_memory = get_redis_memory_in_mb(env)
    env.assertLessEqual(redisearch_memory, redis_memory)
    env.assertEqual(redisearch_memory, vecsim_memory)
    vector = np.float32(np.random.random((1, dimension)))

    # Add vector.
    conn.execute_command('HSET', 1, vector_field, vector.tobytes())
    # Verify current memory readings > previous memory readings.
    cur_redisearch_memory = get_redisearch_vector_index_memory(env, index_key=index_key)
    env.assertLessEqual(redisearch_memory, cur_redisearch_memory)
    cur_vecsim_memory = get_vecsim_memory(env, index_key=index_key, field_name=vector_field)
    env.assertLessEqual(vecsim_memory, cur_vecsim_memory)
    redis_memory = get_redis_memory_in_mb(env)
    redisearch_memory = cur_redisearch_memory
    vecsim_memory = cur_vecsim_memory
    # Verify redis memory >= redisearch index memory
    env.assertLessEqual(redisearch_memory, redis_memory)
    #verify vecsim memory == redisearch memory
    env.assertEqual(cur_vecsim_memory, cur_redisearch_memory)

    # Add vector.
    conn.execute_command('HSET', 2, vector_field, vector.tobytes())
    # Verify current memory readings > previous memory readings.
    cur_redisearch_memory = get_redisearch_vector_index_memory(env, index_key=index_key)
    env.assertLessEqual(redisearch_memory, cur_redisearch_memory)
    cur_vecsim_memory = get_vecsim_memory(env, index_key=index_key, field_name=vector_field)
    env.assertLessEqual(vecsim_memory, cur_vecsim_memory)
    redis_memory = get_redis_memory_in_mb(env)
    redisearch_memory = cur_redisearch_memory
    vecsim_memory = cur_vecsim_memory
    # Verify redis memory >= redisearch index memory
    env.assertLessEqual(redisearch_memory, redis_memory)
    #verify vecsim memory == redisearch memory
    env.assertEqual(cur_vecsim_memory, cur_redisearch_memory)

    # Delete vector
    conn.execute_command('DEL', 2)
    # Verify current memory readings < previous memory readings.
    cur_redisearch_memory = get_redisearch_vector_index_memory(env, index_key=index_key)
    env.assertLessEqual(cur_redisearch_memory, redisearch_memory)
    cur_vecsim_memory = get_vecsim_memory(env, index_key=index_key, field_name=vector_field)
    env.assertLessEqual(cur_vecsim_memory, vecsim_memory)
    redis_memory = get_redis_memory_in_mb(env)
    redisearch_memory = cur_redisearch_memory
    vecsim_memory = cur_vecsim_memory
    # Verify redis memory >= redisearch index memory
    env.assertLessEqual(redisearch_memory, redis_memory)
    #verify vecsim memory == redisearch memory
    env.assertEqual(cur_vecsim_memory, cur_redisearch_memory)

    # Delete vector
    conn.execute_command('DEL', 1)
    # Verify current memory readings < previous memory readings.
    cur_redisearch_memory = get_redisearch_vector_index_memory(env, index_key=index_key)
    env.assertLessEqual(cur_redisearch_memory, redisearch_memory)
    cur_vecsim_memory = get_vecsim_memory(env, index_key=index_key, field_name=vector_field)
    env.assertLessEqual(cur_vecsim_memory, vecsim_memory)
    redis_memory = get_redis_memory_in_mb(env)
    redisearch_memory = cur_redisearch_memory
    vecsim_memory = cur_vecsim_memory
    # Verify redis memory >= redisearch index memory
    env.assertLessEqual(redisearch_memory, redis_memory)
    #verify vecsim memory == redisearch memory
    env.assertEqual(cur_vecsim_memory, cur_redisearch_memory)


def test_hybrid_query_batches_mode_with_text(env):
    conn = getConnectionByEnv(env)
    dimension = 128
    qty = 100
    conn.execute_command('FT.CREATE', 'idx', 'SCHEMA', 'v', 'VECTOR', 'HNSW', '6', 'TYPE', 'FLOAT32',
                         'DIM', dimension, 'DISTANCE_METRIC', 'L2', 't', 'TEXT')
    load_vectors_into_redis(conn, 'v', dimension, qty)
    query_data = np.float32([qty for j in range(dimension)])
    expected_res_1 = [10L, '100', ['__v_score', '0', 't', 'text value'], '99', ['__v_score', '128', 't', 'text value'], '98', ['__v_score', '512', 't', 'text value'], '97', ['__v_score', '1152', 't', 'text value'], '96', ['__v_score', '2048', 't', 'text value'], '95', ['__v_score', '3200', 't', 'text value'], '94', ['__v_score', '4608', 't', 'text value'], '93', ['__v_score', '6272', 't', 'text value'], '92', ['__v_score', '8192', 't', 'text value'], '91', ['__v_score', '10368', 't', 'text value']]
    env.expect('FT.SEARCH', 'idx', '(@t:(text value))=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score',
               'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_1)
    env.expect('FT.SEARCH', 'idx', '(text value)=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score',
               'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_1)
    env.expect('FT.SEARCH', 'idx', '("text value")=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score',
               'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_1)

    # change the text value to 'other' for 10 vectors (with id 10, 20, ..., 100)
    for i in range(1, 11):
        vector = np.float32([10*i for j in range(dimension)])
        conn.execute_command('HSET', 10*i, 'v', vector.tobytes(), 't', 'other')

    # expect to get only vector that passes the filter (i.e, has "other" in t field)
    expected_res_2 = [10L, '100', ['__v_score', '0', 't', 'other'], '90', ['__v_score', '12800', 't', 'other'], '80', ['__v_score', '51200', 't', 'other'], '70', ['__v_score', '115200', 't', 'other'], '60', ['__v_score', '204800', 't', 'other'], '50', ['__v_score', '320000', 't', 'other'], '40', ['__v_score', '460800', 't', 'other'], '30', ['__v_score', '627200', 't', 'other'], '20', ['__v_score', '819200', 't', 'other'], '10', ['__v_score', '1036800', 't', 'other']]
    env.expect('FT.SEARCH', 'idx', '(@t:other)=>[TOP_K 10 @v $vec_param]',
                               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
                               'RETURN', 2, '__v_score', 't').equal(expected_res_2)

    expected_res_3 = [10L, '100', ['__v_score', '0', 't', 'other'], '99', ['__v_score', '128', 't', 'text value'], '98', ['__v_score', '512', 't', 'text value'], '97', ['__v_score', '1152', 't', 'text value'], '96', ['__v_score', '2048', 't', 'text value'], '95', ['__v_score', '3200', 't', 'text value'], '94', ['__v_score', '4608', 't', 'text value'], '93', ['__v_score', '6272', 't', 'text value'], '92', ['__v_score', '8192', 't', 'text value'], '91', ['__v_score', '10368', 't', 'text value']]
    env.expect('FT.SEARCH', 'idx', '(@t:other|text)=>[TOP_K 10 @v $vec_param]',
                         'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
                         'RETURN', 2, '__v_score', 't').equal(expected_res_3)

    # Expect empty score for the intersection (disjoint sets of results)
    env.expect('FT.SEARCH', 'idx', '(@t:other text)=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal([0L])

    # Expect the same results as in expected_res_2 ('other AND NOT text`)
    env.expect('FT.SEARCH', 'idx', '(@t:other -text)=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_2)

    # Expect for top 10 results from vector search that still has the original text "text value"
    # (i.e., expected_res_1 without 100, and with 89 instead)
    expected_res_4 = [10L, '99', ['__v_score', '128', 't', 'text value'], '98', ['__v_score', '512', 't', 'text value'], '97', ['__v_score', '1152', 't', 'text value'], '96', ['__v_score', '2048', 't', 'text value'], '95', ['__v_score', '3200', 't', 'text value'], '94', ['__v_score', '4608', 't', 'text value'], '93', ['__v_score', '6272', 't', 'text value'], '92', ['__v_score', '8192', 't', 'text value'], '91', ['__v_score', '10368', 't', 'text value'], '89', ['__v_score', '15488', 't', 'text value']]
    env.expect('FT.SEARCH', 'idx', '(-(@t:other))=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_4)
    env.expect('FT.SEARCH', 'idx', '(te*)=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, '__v_score', 't').equal(expected_res_4)

    # All documents should match, so TOP 10 takes the 10 with the largest ids. Since we sort by score
    # and "value" is optional, expect that 100 will come first, and the rest will be sorted by id in ascending order.
    expected_res_5 = [10L, '100', '3', ['__v_score', '0', 't', 'other'], '91', '2', ['__v_score', '10368', 't', 'text value'], '92', '2', ['__v_score', '8192', 't', 'text value'], '93', '2', ['__v_score', '6272', 't', 'text value'], '94', '2', ['__v_score', '4608', 't', 'text value'], '95', '2', ['__v_score', '3200', 't', 'text value'], '96', '2', ['__v_score', '2048', 't', 'text value'], '97', '2', ['__v_score', '1152', 't', 'text value'], '98', '2', ['__v_score', '512', 't', 'text value'], '99', '2', ['__v_score', '128', 't', 'text value']]
    env.expect('FT.SEARCH', 'idx', '((text ~value)|other)=>[TOP_K 10 @v $vec_param]', 'WITHSCORES',
               'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, 't', '__v_score').equal(expected_res_5)

    # Same as above, but here we use fuzzy for 'text'
    expected_res_6 = [10L, '100', '3', ['__v_score', '0', 't', 'other'], '91', '1', ['__v_score', '10368', 't', 'text value'], '92', '1', ['__v_score', '8192', 't', 'text value'], '93', '1', ['__v_score', '6272', 't', 'text value'], '94', '1', ['__v_score', '4608', 't', 'text value'], '95', '1', ['__v_score', '3200', 't', 'text value'], '96', '1', ['__v_score', '2048', 't', 'text value'], '97', '1', ['__v_score', '1152', 't', 'text value'], '98', '1', ['__v_score', '512', 't', 'text value'], '99', '1', ['__v_score', '128', 't', 'text value']]
    env.expect('FT.SEARCH', 'idx', '(%test%|other)=>[TOP_K 10 @v $vec_param]', 'WITHSCORES',
               'PARAMS', 2, 'vec_param', query_data.tobytes(),
               'RETURN', 2, 't', '__v_score').equal(expected_res_6)

    # This time the fuzzy matching should not return documents with 'text'.
    env.expect('FT.SEARCH', 'idx', '(%tesst%|other)=>[TOP_K 10 @v $vec_param]',
               'SORTBY', '__v_score', 'PARAMS', 2, 'vec_param', query_data.tobytes(), 'LIMIT', 0, 15,
               'RETURN', 2, 't', '__v_score').equal(expected_res_2)

