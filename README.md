## CouncilCount

This repository holds the code responsible for deploying CouncilCount, a tool allowing users to view demographic data along different NYC geographic boundaries. This repo only holds the data and code necessary for running the dashboard locally or on a server. Please visit [this repo](https://github.com/NewYorkCityCouncil/demo-estimates-by-geo-boundary/tree/main) to access all of the code involved in creating CouncilCount from start to finish, as well as a more in-depth description of the data sources and methodology. Click [here](http://rnd.council.nyc.gov/councilcount/) to access the dashboard.

***

#### Scripts

---
1. Clone the repository:
   ```sh
   git clone https://github.com/NewYorkCityCouncil/councilcount_dashboard_code
   ```
2. Navigate to the project directory:
   ```sh
   cd councilcount_dashboard_code
   ```
---
#### To run via a Docker container on your machine (recommended)

1. Download and start [Docker Desktop](https://www.docker.com/products/docker-desktop/)
2. Run the following commands:

```bash
docker build -t councilcount_dashboard .
docker run -p 8056:8056 councilcount_dashboard
```

---

#### To run locally on your machine without a container
1. Create a virtual environment:
   ```sh
   python3 -m venv myvenv
   ```

2. Actiate a virtual environment:
   ```sh
   source myvenv/bin/activate
   ```

3. Install requirements.txt on your virtual environment:
   ```sh
   pip install -r requirements.txt
   ```

4. Install the required dependencies:
  ```sh
  pip install -r requirements.txt
  ```

5. Navigate to the `code` directory:
  ```sh
  cd code
  ```

6. Run the application:
  ```sh
  python3 councilcount_dashboard.py
  ```

---

#### To run on the server

Use the `--server` flag when executing the script:

```bash
python3 councilcount_dashboard.py --server
```

---

#### To run on a specific port and host

You can specify the host and port using the `--host` and `--port` flags:

```bash
python3 councilcount_dashboard.py --host 0.0.0.0 --port 8080
```

---

Note: All data needed to run the dashboard can be found in /data/output/. Each ACS 5-Year has its own folder.
