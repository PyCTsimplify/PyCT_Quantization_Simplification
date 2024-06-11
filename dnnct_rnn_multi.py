import time
from multiprocessing import Process

# model_name = "stock_LSTM_DenseF_day20_09262"
# model_name = "mnist_lstm_09785"
# model_name = "mnist_sep_act_m6_9653_noise"
# model_name = "stock_LSTM_08804"
# model_name = "stock_LSTM_DenseF_day20_09262"
model_name = "imdb_LSTM_08509"
# model_name="IMDB_transformer_83905"
# model_name = 'mnist_lstm_2'
# model_name = 'mnist_lstm_backdoor'
# model_name = 'sentiment-lstm'
# model_name = 'mnist_lstm'



NUM_PROCESS = 6
# TIMEOUT = 18000
# TIMEOUT = 7200
TIMEOUT = 7200
# TIMEOUT=86400
# TIMEOUT = 172800
NORM_01 = False

if __name__ == "__main__":
    from utils.pyct_attack_exp import run_multi_attack_subprocess_wall_timeout
    from utils.pyct_attack_exp_research_question import (        
        stock_shap_1_2_3_4_8_limit_range02,imdb_shap_1_2_3_4_8_range02,imdb_transformer_shap_1_2_3_4_8_range02,mnist_lstm_1_2_3_4_8_range02,mnist_lstm_15_1_2_3_4_8_range02,sentiment_lstm_lstm_15_1_2_3_4_8_range02
    )
    # inputs = pyct_lstm_stock_1_4_8_16_32_only_first_forward(model_name, first_n_img=502)
    # inputs = pyct_lstm_stock_1_2_3_4_8_limit_range02(model_name, first_n_img=502)
    # inputs = stock_shap_1_2_3_4_8_limit_range02(model_name, first_n_img=60)
    #嗨我是其瑞
    model_type="tnn"
    inputs = imdb_shap_1_2_3_4_8_range02(model_name, first_n_img=30,model_type=model_type)
    print("#"*40, f"number of inputs: {len(inputs)}", "#"*45)
    time.sleep(3)

    ########## 分派input給各個subprocesses ##########    
    all_subprocess_tasks = [[] for _ in range(NUM_PROCESS)]
    cursor = 0
    for task in inputs:    
        all_subprocess_tasks[cursor].append(task)    
       
        cursor+=1
        if cursor == NUM_PROCESS:
            cursor = 0


    running_processes = []
    for sub_tasks in all_subprocess_tasks:
        if len(sub_tasks) > 0:
            p = Process(target=run_multi_attack_subprocess_wall_timeout, args=(sub_tasks, TIMEOUT, NORM_01,model_type))
            p.start()
            running_processes.append(p)
            time.sleep(1) # subprocess start 的間隔時間
       
    for p in running_processes:
        p.join()

    print('done')
