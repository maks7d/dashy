from flask import Flask, jsonify
import psutil
import subprocess

app = Flask(__name__)

def get_system_metrics():
    metrics = {
        'cpu_usage': psutil.cpu_percent(interval=1),
        'ram_usage': psutil.virtual_memory().percent,
        'disk_usage': psutil.disk_usage('/').percent,
        'network_io': {
            'bytes_sent': psutil.net_io_counters().bytes_sent,
            'bytes_recv': psutil.net_io_counters().bytes_recv
        }
    }
    return metrics

def get_gpu_metrics():
    try:
        result = subprocess.check_output(['nvidia-smi', '--query-gpu=temperature.gpu,utilization.gpu,power.draw', '--format=csv,noheader,nounits'])
        temperature, utilization, power_draw = result.decode().strip().split(', ')
        return {
            'gpu_temperature': float(temperature),
            'gpu_utilization': float(utilization),
            'gpu_power_draw': float(power_draw)
        }
    except Exception as e:
        return {'error': str(e)}

@app.route('/metrics', methods=['GET'])
def metrics():
    system_metrics = get_system_metrics()
    gpu_metrics = get_gpu_metrics()
    all_metrics = {**system_metrics, **gpu_metrics}
    return jsonify(all_metrics)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
