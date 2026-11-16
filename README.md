# Translating Java RMI Architecture to Python Distributed Objects (Pyro5)

> **Distributed Systems Laboratory**  
> **Reference Architecture:** [Sunway DPP Java RMI Lab (JAVA_RMI_IV)](https://github.com/nix1947/sunway_dpp/tree/master/JAVA_RMI_IV)  
> **Target Implementation:** Python 3.10+ with [Pyro5 (Python Remote Objects)](https://pyro5.readthedocs.io/)

---

## 1. Project Overview

This project analyzes the multi-file **Java Remote Method Invocation (RMI)** distributed object architecture from `JAVA_RMI_IV` and translates it into an equivalent, idiomatic **Python distributed object system** using **Pyro5**.

In distributed object computing, a client invokes methods on an object residing in a different address space (or physical machine) as though the object were local. This laboratory demonstrates how classical Java RMI paradigms—remote interfaces, skeletons/daemons, registries, and dynamic stubs/proxies—map directly to Python Pyro5 constructs.

---

## 2. Architectural Translation Matrix (Java RMI vs. Python Pyro5)

The table below details how each component in the Java RMI reference implementation is mapped to the Python Pyro5 distributed lab:

| Architectural Role | Java RMI (`JAVA_RMI_IV`) | Python Pyro5 (`PYTHON_RMI_LAB`) | Semantic Equivalence |
|---|---|---|---|
| **Remote Interface** | `Product.java`<br>`public interface Product extends Remote` | `product.py`<br>`Product` model & explicit `@Pyro5.api.expose` methods | Defines the remote contract (methods callable across the network: `getName()`, `getDescription()`, `getPrice()`). |
| **Remote Implementation** | `ProductImpl.java`<br>`extends UnicastRemoteObject implements Product` | `server.py`<br>`@Pyro5.api.expose`<br>`class ProductImpl` | Encapsulates the actual business logic and state. Executes on the server process when invoked remotely. |
| **Server Skeleton & Daemon** | `ServerImpl.java`<br>`extends UnicastRemoteObject implements Server` | `server.py`<br>`Pyro5.api.Daemon` | The network listener dispatching incoming remote RPC requests to the target object instances. |
| **Registry & Object Publishing** | `rmiregistry`<br>`Naming.rebind("rmi://localhost:9000/laptop", stub)` | `server.py`<br>`daemon.register(obj, objectId="laptop")`<br>generates `PYRO:laptop@host:port` | Associates a human-readable identifier (object ID) with a network-accessible remote object instance. |
| **Client Proxy Lookup** | `Client.java`<br>`LocateRegistry.getRegistry("127.0.0.1", 9000)`<br>`(Product) registry.lookup("laptop")` | `client.py`<br>`Pyro5.api.Proxy("PYRO:laptop@127.0.0.1:9090")` | Resolves the remote object reference and constructs a client-side proxy (stub) that transparently serializes calls. |
| **Remote Method Invocation** | `stub.getName()`<br>`stub.getDescription()`<br>`stub.getPrice()` | `proxy.getName()`<br>`proxy.getDescription()`<br>`proxy.getPrice()` | Transparent RPC execution across process boundaries; return values are serialized and returned to the caller. |
| **Network Exception Handling** | `catch (RemoteException e)` | `except Pyro5.errors.CommunicationError:`<br>`except Pyro5.errors.PyroError:` | Traps communication dropouts, server offline conditions, or remote runtime faults gracefully. |

---

## 3. Repository Structure

Adhering strictly to the suggested lab organization from `instruction.md`:

```text
Translating Java RMI Architecture to Python Distributed Objects/
├── PYTHON_RMI_LAB/
│   ├── __init__.py
│   ├── product.py              # Equivalent to Product.java (Data model & contracts)
│   ├── server.py               # Equivalent to Server.java, ProductImpl.java, ServerImpl.java
│   ├── client.py               # Equivalent to Client.java (Proxy lookup & remote calls)
│   ├── requirements.txt        # Core dependencies (Pyro5)
│   └── tests/
│       ├── __init__.py
│       ├── test_product.py     # Unit tests for Product serialization & attributes
│       ├── test_server.py      # Unit tests for daemon registration & catalog
│       ├── test_client.py      # Tests for proxy lookups & error handling
│       └── test_integration.py # Multi-process E2E integration test suite
├── screenshots/                # Deliverable [1] terminal output screenshots
├── run_demo.bat                # Windows one-click dual-terminal demo launcher
├── run_demo.ps1                # PowerShell one-click dual-terminal demo launcher
├── .gitignore                  # Git exclusions (bytecode, environments, IDE caches)
└── README.md                   # This authoritative documentation guide
```

---

## 4. Setup and Installation

### Prerequisites
- **Python 3.10+** (Tested on Python 3.10, 3.11, 3.12, 3.13, 3.14)
- **pip** package manager

### 1. Clone the Repository
```bash
git clone https://github.com/loisycalo132102-web/Translating-Java-RMI-Architecture-to-Python-Distributed-Objects.git
cd "Translating-Java-RMI-Architecture-to-Python-Distributed-Objects"
```

### 2. Create and Activate a Virtual Environment (Recommended)

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r PYTHON_RMI_LAB/requirements.txt
```

*(Optional for running tests: `pip install pytest`)*

---

## 5. Dual-Terminal Execution Walkthrough

The lab requires running the server and client across separate terminals to demonstrate distributed object invocation.

### Terminal 1: Run the Server Daemon

Open your first terminal and start the Pyro5 server daemon:

```bash
python PYTHON_RMI_LAB/server.py
```

**Custom Host/Port Options:**
```bash
python PYTHON_RMI_LAB/server.py --host 127.0.0.1 --port 9090
```

**Expected Terminal 1 Output:**
```text
============================================================
Server is booting....
Target host: 127.0.0.1:9090
============================================================

Registered Remote Objects (Java RMI equivalent):
  • LAPTOP   -> PYRO:laptop@127.0.0.1:9090
  • RAM      -> PYRO:ram@127.0.0.1:9090
  • BAG      -> PYRO:bag@127.0.0.1:9090
  • CHARGER  -> PYRO:charger@127.0.0.1:9090

[Server] Ready to accept remote method invocations.
[Server] Press Ctrl+C to stop server.
------------------------------------------------------------
```

---

### Terminal 2: Run the Distributed Client

Open your second terminal and execute the client to query the remote server:

#### A. Query the Entire Product Catalog
```bash
python PYTHON_RMI_LAB/client.py
```

**Expected Terminal 2 Output:**
```text
=================================================================
Connecting to Distributed RMI Server at 127.0.0.1:9090...
Equivalent to: LocateRegistry.getRegistry() & registry.lookup()
=================================================================

Successfully queried 4 remote product object(s):

OBJECT ID    | PRODUCT NAME       | PRICE      | DESCRIPTION
-----------------------------------------------------------------
LAPTOP       | Laptop             | $800000.00 | Lenovo laptop
RAM          | Mobile             | $24000.00  | MI 9 mobile
BAG          | Bag                | $800.00    | Branded bag
CHARGER      | Charger            | $230.00    | MI Charger
-----------------------------------------------------------------
[Client] All remote method invocations completed successfully.
```

#### B. Query a Single Product Stub (e.g., `laptop` or `ram`)
```bash
python PYTHON_RMI_LAB/client.py --item laptop
```

**Expected Output:**
```text
=================================================================
Connecting to Distributed RMI Server at 127.0.0.1:9090...
Equivalent to: LocateRegistry.getRegistry() & registry.lookup()
=================================================================

Successfully queried 1 remote product object(s):

OBJECT ID    | PRODUCT NAME       | PRICE      | DESCRIPTION
-----------------------------------------------------------------
LAPTOP       | Laptop             | $800000.00 | Lenovo laptop
-----------------------------------------------------------------
[Client] All remote method invocations completed successfully.
```

---

## 6. Offline / Error Resilience Demonstration

When the server daemon is not active, the client gracefully handles the connection failure without a crash:

```bash
python PYTHON_RMI_LAB/client.py --port 9999
```

**Output:**
```text
=================================================================
Connecting to Distributed RMI Server at 127.0.0.1:9999...
Equivalent to: LocateRegistry.getRegistry() & registry.lookup()
=================================================================
[Client Error] Failed to connect to remote object 'laptop' at 127.0.0.1:9999: [WinError 10061] No connection could be made because the target machine actively refused it
...
[Error] Could not connect or retrieve any products from server at 127.0.0.1:9999.
[Tip] Ensure the server is running: python PYTHON_RMI_LAB/server.py
```

---

## 7. Automated Test Suite

A comprehensive test suite is provided to verify each component individually and end-to-end across separate OS processes:

```bash
python -m pytest PYTHON_RMI_LAB/tests -v
```

### Test Suite Breakdown:
1. **`test_product.py`**: Verifies product attributes, immutability, equality, serialization to dict, and Pyro5/serpent wire compatibility.
2. **`test_server.py`**: Tests server daemon initialization, catalog creation matching `Server.java`, and remote method invocation on `ProductImpl`.
3. **`test_client.py`**: Validates client proxy URI creation, remote queries against live daemon threads, and offline communication error handling.
4. **`test_integration.py`**: Spawns real server and client processes using `subprocess.Popen` on dynamic TCP ports, verifies condition-based socket readiness, asserts standard output formatting, and validates clean teardown.

---

## 8. Lab Deliverables Checklist

- [x] **Source Files:**
  - `PYTHON_RMI_LAB/product.py` (mirrors `Product.java`)
  - `PYTHON_RMI_LAB/server.py` (consolidates `ProductImpl.java`, `Server.java`, `ServerImpl.java`)
  - `PYTHON_RMI_LAB/client.py` (mirrors `Client.java`)
- [x] **Deliverable [1] — Screenshots:**
  - Capture side-by-side terminal windows of **Terminal 1** (`server.py`) and **Terminal 2** (`client.py`) showing successful registration and query output (included in [`screenshots/`](screenshots/)).
- [x] **Deliverable [2] — GitHub Repository:**
  - Public GitHub repository containing complete source code, automated test suite, and this `README.md`.
