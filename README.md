# ARTEKMED Log-Client for OpenObserve

## Installation

#### Clone this repositiory

```
git clone https://github.com/TUM-CAMP-NARVIS/artekmed_zenoh_openobserve_logger.git
```

#### Navigate to your project directory

```
cd artekmed_zenoh_openobserve_logger
```

#### Create the virtual environment

```
python3 -m venv venv
```

#### Activate the virtual environment

On macOS and Linux:

```
source venv/bin/activate
```

On Windows:

```
.\venv\Scripts\activate
```

#### Install dependencies

```
pip install -r requirements.txt
```

#### Set Environment Variables
```
export OPENOBSERVE_NODE_NAME=narvis
```

#### Start application

```
python3 main.py --query tcn/loc/*/*/str/logs
```
