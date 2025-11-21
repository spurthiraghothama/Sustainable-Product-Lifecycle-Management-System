# Sustainable-Product-Lifecycle-Management-System


## Project Overview

The Sustainable Product Lifecycle Management System is a comprehensive digital database designed to manage products, components, raw materials, suppliers, and lifecycle events.

In an era where sustainability and resource efficiency are global priorities, this system acts as a digital record—a "Material Passport"—that follows every product from its design stage to its end-of-life phase. Its primary goal is to provide complete traceability from a finished product back to its raw materials. This transparency supports the principles of a circular economy, ensuring materials are reused, recycled, or disposed of safely, thereby reducing environmental damage and operational costs.

## User Requirement Specification

The system is engineered to manage comprehensive data including:
* Constituent components and their hierarchical assembly.
* Raw materials and their hazardous status.
* Suppliers of specific materials.
* A complete log of significant lifecycle events (manufacturing, repair, recycling).

## Scope
The functional scope involves capturing and relating information across the product's life:
* Product Tracking: Managing generic product models and unique physical instances (Serial Numbers).
* Bill of Materials (BOM): Defining hierarchical parent-child relationships for assemblies.
* Material Composition: Cataloging raw materials, flagging hazardous items, and recording precise weights.
* Supply Chain: Linking suppliers to the specific components or materials they provide.
* Lifecycle Logging: Timestamping events such as manufacturing, inspection, and recycling.

## Target Users

* Manufacturing Engineers: Manage product models and BOM data.
* Procurement Officers: Handle supplier records and sourcing.
* Environmental Compliance Teams: Review material compositions and hazardous flags.
* Recyclers: Access product passports to identify recoverable materials.

## Technical stack
* Database Management System: MySQL
* Query Language: SQL
* Administration Tool: MySQL Workbench
* Frontend Prototyping: HTML, CSS, JavaScript
* Version Control: Git & GitHub

## Database Schema Architecture
The database is normalized and structured around four core areas.

* 1. Core Entities
Products: Stores generic model information.
Components: Stores individual parts used in assemblies.
RawMaterials: Tracks material types, hazardous status, and recyclable grades.
Suppliers: Manages vendor information.

* 2. Instances & Events
ProductInstances: Links specific serial numbers to the generic Product ID.
LifecycleEvents: Records the history (Event Type, Date) for each specific instance.

* 3. Composition & Hierarchy
BillOfMaterial: A recursive table defining parent-child component relationships and quantities.
ComponentComposition: Links components to raw materials with specific weights.

* 4. Sourcing
Sourcing: Connects suppliers to either a Component or a Material using a check constraint to ensure valid data entry.


* **Product Genealogy:** Distinguishes between generic product models and individual serial-numbered instances.
* **Bill of Materials (BOM) Management:** Recursive tracking of product composition (assemblies and sub-assemblies).
* **Material Composition Analysis:** precise tracking of raw material weights and hazardous material flags for compliance.
* **Supply Chain Transparency:** Links suppliers directly to the specific components or raw materials they provide.
* **Lifecycle Logging:** Immutable history of events including Manufacturing, Sales, Repairs, and End-of-Life Disposal.
* **Automated Validation:** Database triggers ensure logical consistency (e.g., preventing the disposal of unsold items).

## Tech Stack

* **Database:** MySQL 8.0+
* **Query Language:** SQL (Structured Query Language)
* **Frontend Interface:** HTML5, CSS3, JavaScript (Vanilla)
* **Tools:** MySQL Workbench, Git

## Database Architecture

The system is built on the following core entities:

1.  **Products:** Stores generic model information.
2.  **ProductInstances:** Tracks individual physical items via Serial Number.
3.  **Components:** Stores distinct parts and assemblies.
4.  **BillOfMaterial:** A junction table defining the parent-child hierarchy of parts.
5.  **RawMaterials:** Stores material properties (Recyclable Grade, Hazardous Status).
6.  **ComponentComposition:** Links components to raw materials by weight.
7.  **Suppliers:** Directory of external vendors.
8.  **Sourcing:** Links vendors to specific parts or materials.
9.  **LifecycleEvents:** Time-series data for product status changes.

## Advanced SQL Implementation

This project utilizes advanced DBMS features to ensure data integrity and automate business logic:

### Triggers
* `Before_Disposal_Check`: Enforces business logic that a product cannot be marked as "Disposed" unless it has previously been "Sold".
* `Before_Hazardous_Material`: Prevents data entry if a single component contains excessive hazardous material (>500g).
* `Before_Lifecycle_Delete`: Automatically backs up lifecycle events to a separate audit table before deletion.

### Stored Procedures
* `RegisterProductInstance`: Atomically creates a product instance and logs its manufacturing timestamp.
* `RecycleProduct`: Analyzes material composition to classify the recycling event (Hazardous vs. Standard).
* `GetProductTrace`: Generates a complete report of all materials within a product.
* `GetLifecycleReport`: Retrieves the chronological history of a specific item.

### Functions
* `GetComponentWeight`: Calculates the total weight of a component based on composition.
* `IsMaterialHazardous`: Boolean check for material safety.
* `GetLifecycleAge`: Calculates the age of a product in days.
* `GetSupplierType`: Categorizes suppliers based on their sourcing history.

## Installation and Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/spurthiraghothama/Sustainable-Product-Lifecycle-Management-System.git
    ```

2.  **Database Setup**
    * Open MySQL Workbench.
    * Open the file `commands.sql` located in the root directory.
    * Execute the script. This will:
        * Create the `circular_economy_db` database.
        * Create all tables and constraints.
        * Insert mock data for testing.
        * Define all functions, procedures, and triggers.

3.  **Frontend Setup**
    * Run app.py


## Team Details

* **SHRUJANNA M** - PES1UG23CS570
* **SPURTHI RAGHOTHAMA** - PES1UG23CS590

## Licensing This project is developed for academic purposes at **PES University**.
