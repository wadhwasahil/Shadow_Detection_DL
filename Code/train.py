import tensorflow as tf
from data_helpers import read_data
from generator import Generator
from discriminator import Discriminator
import os
import time
import numpy as np

with tf.Graph().as_default():
    session_conf = tf.ConfigProto(allow_soft_placement=True, log_device_placement=True)
    sess = tf.Session(config=session_conf)
    with sess.as_default():
        batch_size = 16
        gamma = 0.7
        X = tf.placeholder(tf.float32, [batch_size, 256, 256, 3], name="X")
        ground_truth_shadow_masks = tf.placeholder(tf.float32, [batch_size, 256, 256], name="y")
        global_step = tf.Variable(0, name="global_step", trainable=False)
        optimizer = tf.train.AdamOptimizer(1e-3)

        # Generator
        gen = Generator(X, gamma, batch_size)
        gx = gen.tanh  # shadow mask of size 256 * 256 generated by generator
        t1 = tf.scalar_mul(-gamma, tf.matmul(ground_truth_shadow_masks, tf.log(gx), transpose_a=True))
        t2 = tf.scalar_mul(gamma - 1, tf.matmul((1 - ground_truth_shadow_masks), tf.log(1 - gx), transpose_a=True))

        L_data = -tf.reduce_mean(t1 + t2)

        # Discriminator
        dx_real = Discriminator(X, ground_truth_shadow_masks).sigmoid
        dx_fake = Discriminator(X, gx, reuse=True).sigmoid

        # check1 = tf.log(dx_real) + tf.log(1. - dx_fake)
        L_cGan = -tf.reduce_mean(tf.log(dx_real) + tf.log(1. - dx_fake))

        Lambda = 0.5

        with tf.variable_scope("D_loss"):
            d_loss = L_cGan + Lambda * L_data
            tf.summary.scalar("d_loss", d_loss)

        with tf.variable_scope("G_loss"):
            g_loss = -(L_cGan + Lambda * L_data)
            tf.summary.scalar("g_loss", g_loss)

        tvar = tf.trainable_variables()
        dvar = [var for var in tvar if 'discriminator' in var.name]
        gvar = [var for var in tvar if 'generator' in var.name]

        with tf.name_scope('train'):
            d_train_step = tf.train.AdamOptimizer().minimize(d_loss, var_list=dvar)
            g_train_step = tf.train.AdamOptimizer().minimize(g_loss, var_list=gvar)
        init = tf.global_variables_initializer()
        sess.run(init)
        # out_dir = os.path.abspath(os.path.join(os.path.curdir, "pizza/"))
        # merged_summary = tf.summary.merge_all()
        timestamp = str(int(time.time()))
        # writer = tf.summary.FileWriter(out_dir + timestamp)
        # writer.add_graph(sess.graph)

        for batch in read_data():
            x, y = zip(*batch)
            x = np.array(x)
            y = np.array(y)
            # _, step, dx_real_val, dx_fake_val, d_loss_val = sess.run(
            #     [d_train_step, global_step, dx_real, dx_fake, d_loss],
            #     feed_dict={X: x, ground_truth_shadow_masks: y})
            # _, g_loss = sess.run([g_train_step, g_loss], feed_dict={X:x, ground_truth_shadow_masks:y})
            # print(step, dx_real_val, dx_fake_val, d_loss_val)
            _,  gx, g_loss_val = sess.run([d_train_step, gx, g_loss], feed_dict={X: x})
            print(g_loss_val)

