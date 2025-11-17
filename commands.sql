create database new_circular;
use new_circular;




CREATE TABLE Products (
  ProductID VARCHAR(50) PRIMARY KEY,
  ModelName VARCHAR(100) NOT NULL
);

CREATE TABLE Components (
  ComponentID VARCHAR(50) PRIMARY KEY,
  ComponentName VARCHAR(100) NOT NULL
);

CREATE TABLE RawMaterials (
  MaterialID VARCHAR(50) PRIMARY KEY,
  MaterialName VARCHAR(100) NOT NULL,
  IsHazardous BOOLEAN DEFAULT FALSE,
  RecyclableGrade VARCHAR(20)
);

CREATE TABLE Suppliers (
  SupplierID VARCHAR(50) PRIMARY KEY,
  SupplierName VARCHAR(100) NOT NULL
);

/* ------------------------------------------------------------
   2. PRODUCT INSTANCES & EVENTS
   ------------------------------------------------------------ */

CREATE TABLE ProductInstances (
  InstanceID INT PRIMARY KEY AUTO_INCREMENT,
  SerialNumber VARCHAR(100) NOT NULL UNIQUE,
  ProductID VARCHAR(50) NOT NULL,
  FOREIGN KEY (ProductID) REFERENCES Products(ProductID)
);

CREATE TABLE LifecycleEvents (
  EventID INT PRIMARY KEY AUTO_INCREMENT,
  EventType VARCHAR(50) NOT NULL,
  EventDate DATETIME NOT NULL,
  InstanceID INT NOT NULL,
  FOREIGN KEY (InstanceID) REFERENCES ProductInstances(InstanceID)
);

/* ------------------------------------------------------------
   3. BILL OF MATERIALS & COMPOSITION
   ------------------------------------------------------------ */

CREATE TABLE BillOfMaterial (
  ParentComponentID VARCHAR(50) NOT NULL,
  ChildComponentID VARCHAR(50) NOT NULL,
  Quantity INT NOT NULL,
  PRIMARY KEY (ParentComponentID, ChildComponentID),
  FOREIGN KEY (ParentComponentID) REFERENCES Components(ComponentID),
  FOREIGN KEY (ChildComponentID) REFERENCES Components(ComponentID),
  CHECK (Quantity > 0)
);

CREATE TABLE ComponentComposition (
  ComponentID VARCHAR(50) NOT NULL,
  MaterialID VARCHAR(50) NOT NULL,
  WeightInGrams DECIMAL(10, 2) NOT NULL,
  PRIMARY KEY (ComponentID, MaterialID),
  FOREIGN KEY (ComponentID) REFERENCES Components(ComponentID),
  FOREIGN KEY (MaterialID) REFERENCES RawMaterials(MaterialID),
  CHECK (WeightInGrams > 0)
);

/* ------------------------------------------------------------
   4. SOURCING (Supplier → Component OR Material)
   ------------------------------------------------------------ */

CREATE TABLE Sourcing (
  SourcingID INT PRIMARY KEY AUTO_INCREMENT,
  SupplierID VARCHAR(50) NOT NULL,
  ComponentID VARCHAR(50),
  MaterialID VARCHAR(50),
  FOREIGN KEY (SupplierID) REFERENCES Suppliers(SupplierID),
  FOREIGN KEY (ComponentID) REFERENCES Components(ComponentID),
  FOREIGN KEY (MaterialID) REFERENCES RawMaterials(MaterialID),
  CONSTRAINT chk_sourcing_type CHECK (
    (ComponentID IS NOT NULL AND MaterialID IS NULL) OR
    (ComponentID IS NULL AND MaterialID IS NOT NULL)
  )
);

/* ============================================================
   DATA INSERTION SECTION
   ============================================================ */

/* -------------------------
   Products
   ------------------------- */

INSERT INTO Products (ProductID, ModelName) VALUES
('P100', 'Alpha Laptop 15-inch'),
('P200', 'Eco Smartphone Model 5');

/* -------------------------
   Components
   ------------------------- */

INSERT INTO Components (ComponentID, ComponentName) VALUES
('C100', 'Alpha Laptop Main Assembly'),
('C101', '15-inch Screen Unit'),
('C102', 'Laptop Keyboard'),
('C103', '50Wh Battery Pack'),
('C200', 'Eco Phone Main Assembly'),
('C201', '5.8-inch OLED Screen'),
('C202', '25Wh Battery Pack'),
('C300', 'Universal Logic Board');

/* -------------------------
   Raw Materials
   ------------------------- */

INSERT INTO RawMaterials (MaterialID, MaterialName, IsHazardous, RecyclableGrade) VALUES
('M1', 'Aluminum', 0, 'A'),
('M2', 'Plastic (ABS)', 0, 'C'),
('M3', 'Lithium-Ion', 1, 'D'),
('M4', 'Glass (Gorilla)', 0, 'B'),
('M5', 'Silicon', 0, 'B');

/* -------------------------
   Suppliers
   ------------------------- */

INSERT INTO Suppliers (SupplierID, SupplierName) VALUES
('S1', 'Global Components Inc.'),
('S2', 'EcoMaterials Ltd.'),
('S3', 'Pure Metals Co.');

/* -------------------------
   Product Instances
   ------------------------- */

INSERT INTO ProductInstances (SerialNumber, ProductID) VALUES
('ALPHA-0001', 'P100'),
('ALPHA-0002', 'P100'),
('ECO-0001', 'P200'),
('ECO-0002', 'P200');

/* -------------------------
   Bill of Materials
   ------------------------- */

INSERT INTO BillOfMaterial (ParentComponentID, ChildComponentID, Quantity) VALUES
('C100', 'C101', 1),
('C100', 'C102', 1),
('C100', 'C103', 1),
('C100', 'C300', 1),
('C200', 'C201', 1),
('C200', 'C202', 1),
('C200', 'C300', 1);

/* -------------------------
   Component Material Composition
   ------------------------- */

INSERT INTO ComponentComposition (ComponentID, MaterialID, WeightInGrams) VALUES
('C101', 'M4', 150.0),
('C101', 'M2', 50.0),
('C102', 'M2', 200.0),
('C103', 'M3', 300.0),
('C103', 'M1', 50.0),
('C201', 'M4', 50.0),
('C202', 'M3', 100.0),
('C300', 'M5', 25.0);

/* -------------------------
   Sourcing
   ------------------------- */

INSERT INTO Sourcing (SupplierID, ComponentID, MaterialID) VALUES
('S1', 'C101', NULL),
('S1', 'C300', NULL),
('S2', NULL, 'M2'),
('S2', NULL, 'M4'),
('S3', NULL, 'M1'),
('S3', NULL, 'M3');

/* -------------------------
   Lifecycle Events
   ------------------------- */

INSERT INTO LifecycleEvents (EventType, EventDate, InstanceID) VALUES
('Manufactured', '2024-01-01', 1),
('Sold', '2024-01-15', 1),
('Repair', '2025-03-15', 1),
('Disposed', '2025-10-20', 1),
('Manufactured', '2024-01-02', 2),
('Sold', '2024-01-18', 2),
('Recycled', '2025-10-22', 2),
('Manufactured', '2024-02-01', 3),
('Sold', '2024-02-10', 3),
('Recycled', '2025-10-25', 3),
('Manufactured', '2024-02-02', 4),
('Sold', '2024-02-11', 4),
('Disposed', '2025-09-01', 4);


/* ============================================================
   FUNCTIONS
   ============================================================ */

DELIMITER //

/* Returns total material weight of a component */
CREATE FUNCTION GetComponentWeight(compID VARCHAR(50))
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
  DECLARE total DECIMAL(10,2);
  SELECT SUM(WeightInGrams) INTO total
  FROM ComponentComposition
  WHERE ComponentID = compID;
  RETURN IFNULL(total, 0);
END //

/* Count number of subcomponents */
CREATE FUNCTION GetProductTotalComponents(parentComp VARCHAR(50))
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE cnt INT;
  SELECT COUNT(*) INTO cnt
  FROM BillOfMaterial
  WHERE ParentComponentID = parentComp;
  RETURN IFNULL(cnt, 0);
END //

/* Check if material is hazardous */
CREATE FUNCTION IsMaterialHazardous(matID VARCHAR(50))
RETURNS BOOLEAN
DETERMINISTIC
BEGIN
  DECLARE flag BOOLEAN;
  SELECT IsHazardous INTO flag FROM RawMaterials WHERE MaterialID = matID;
  RETURN IFNULL(flag, FALSE);
END //

/* Supplier type determination */
CREATE FUNCTION GetSupplierType(suppID VARCHAR(50))
RETURNS VARCHAR(20)
DETERMINISTIC
BEGIN
  DECLARE cntComp INT;
  DECLARE cntMat INT;

  SELECT COUNT(*) INTO cntComp
  FROM Sourcing
  WHERE SupplierID = suppID AND ComponentID IS NOT NULL;

  SELECT COUNT(*) INTO cntMat
  FROM Sourcing
  WHERE SupplierID = suppID AND MaterialID IS NOT NULL;

  IF cntComp > 0 AND cntMat > 0 THEN
    RETURN 'Both';
  ELSEIF cntComp > 0 THEN
    RETURN 'Component Supplier';
  ELSEIF cntMat > 0 THEN
    RETURN 'Material Supplier';
  ELSE
    RETURN 'Unknown';
  END IF;
END //

/* Grade to numeric recyclability score */
CREATE FUNCTION GetRecyclableScore(grade VARCHAR(5))
RETURNS INT
DETERMINISTIC
BEGIN
  RETURN CASE grade
    WHEN 'A' THEN 4
    WHEN 'B' THEN 3
    WHEN 'C' THEN 2
    WHEN 'D' THEN 1
    ELSE 0
  END;
END //

/* Calculate age in days since manufactured */
CREATE FUNCTION GetLifecycleAge(instID INT)
RETURNS INT
DETERMINISTIC
BEGIN
  DECLARE manuDate DATE;

  SELECT DATE(EventDate)
  INTO manuDate
  FROM LifecycleEvents
  WHERE InstanceID = instID AND EventType = 'Manufactured'
  ORDER BY EventDate ASC
  LIMIT 1;

  RETURN DATEDIFF(CURDATE(), manuDate);
END //

/* Returns comma-separated list of subcomponent names */
CREATE FUNCTION GetComponentDetails(parentComp VARCHAR(50))
RETURNS TEXT
DETERMINISTIC
BEGIN
  DECLARE subcomponents TEXT;

  SELECT GROUP_CONCAT(c.ComponentName SEPARATOR ', ')
  INTO subcomponents
  FROM BillOfMaterial b
  JOIN Components c ON b.ChildComponentID = c.ComponentID
  WHERE b.ParentComponentID = parentComp;

  RETURN IFNULL(subcomponents, 'No subcomponents');
END //

/* Return detailed summary: count + names + quantities */
CREATE FUNCTION GetComponentSummary(parentComp VARCHAR(50))
RETURNS TEXT
DETERMINISTIC
BEGIN
  DECLARE total INT DEFAULT 0;
  DECLARE sublist TEXT;

  SELECT COUNT(*) INTO total
  FROM BillOfMaterial
  WHERE ParentComponentID = parentComp;

  SELECT GROUP_CONCAT(CONCAT(c.ComponentName, ' (x', b.Quantity, ')') SEPARATOR ', ')
  INTO sublist
  FROM BillOfMaterial b
  JOIN Components c ON b.ChildComponentID = c.ComponentID
  WHERE b.ParentComponentID = parentComp;

  RETURN IFNULL(CONCAT(total, ' subcomponents: ',
           IFNULL(sublist, 'No subcomponents')),
         'No subcomponents');
END //

DELIMITER ;

/* ============================================================
   STORED PROCEDURES
   ============================================================ */

DELIMITER //

/* Register product + auto manufacturing event */
CREATE PROCEDURE RegisterProductInstance(
  IN pSerial VARCHAR(100),
  IN pProductID VARCHAR(50)
)
BEGIN
  INSERT INTO ProductInstances (SerialNumber, ProductID)
  VALUES (pSerial, pProductID);

  CALL AddLifecycleEvent(LAST_INSERT_ID(), 'Manufactured');
END //

/* Insert lifecycle event */
CREATE PROCEDURE AddLifecycleEvent(IN pInstanceID INT, IN pEventType VARCHAR(50))
BEGIN
  INSERT INTO LifecycleEvents (EventType, EventDate, InstanceID)
  VALUES (pEventType, NOW(), pInstanceID);
END //

/* Log recycling + hazardous check */
CREATE PROCEDURE RecycleProduct(IN instID INT)
BEGIN
  DECLARE hazCount INT;

  SELECT COUNT(*) INTO hazCount
  FROM ComponentComposition cc
  JOIN BillOfMaterial bom ON cc.ComponentID = bom.ChildComponentID
  WHERE cc.MaterialID IN (
    SELECT MaterialID FROM RawMaterials WHERE IsHazardous = 1
  );

  IF hazCount > 0 THEN
    INSERT INTO LifecycleEvents(EventType, EventDate, InstanceID)
    VALUES ('Recycled_Hazardous', NOW(), instID);
  ELSE
    INSERT INTO LifecycleEvents(EventType, EventDate, InstanceID)
    VALUES ('Recycled', NOW(), instID);
  END IF;
END //

/* Trace product composition */
CREATE PROCEDURE GetProductTrace(IN pProductID VARCHAR(50))
BEGIN
  SELECT c.ComponentName, rm.MaterialName,
         cc.WeightInGrams, rm.RecyclableGrade
  FROM Components c
  JOIN BillOfMaterial bom ON bom.ChildComponentID = c.ComponentID
  JOIN ComponentComposition cc ON cc.ComponentID = c.ComponentID
  JOIN RawMaterials rm ON rm.MaterialID = cc.MaterialID;
END //

/* Add new supplier */
CREATE PROCEDURE AddNewSupplier(IN sID VARCHAR(50), IN sName VARCHAR(100))
BEGIN
  INSERT INTO Suppliers(SupplierID, SupplierName)
  VALUES (sID, sName);
END //

/* Summary of supplier items */
CREATE PROCEDURE GetSupplierSummary(IN sID VARCHAR(50))
BEGIN
  SELECT SupplierName, ComponentID, MaterialID
  FROM Sourcing JOIN Suppliers USING(SupplierID)
  WHERE SupplierID = sID;
END //

/* Add material weight safely */
CREATE PROCEDURE AddMaterialComposition(
  IN cID VARCHAR(50),
  IN mID VARCHAR(50),
  IN w DECIMAL(10,2)
)
BEGIN
  IF w <= 0 THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Invalid weight value';
  ELSE
    INSERT INTO ComponentComposition(ComponentID, MaterialID, WeightInGrams)
    VALUES (cID, mID, w);
  END IF;
END //

/* Lifecycle report */
CREATE PROCEDURE GetLifecycleReport(IN instID INT)
BEGIN
  SELECT EventType,
         DATE_FORMAT(EventDate, '%Y-%m-%d %H:%i') AS EventTime
  FROM LifecycleEvents
  WHERE InstanceID = instID
  ORDER BY EventDate;
END //

DELIMITER ;

/* ============================================================
   TRIGGERS
   ============================================================ */

/* Backup table for lifecycle deletes */
CREATE TABLE LifecycleBackup LIKE LifecycleEvents;

DELIMITER //

/* Prevent disposal before sale */
CREATE TRIGGER Before_Disposal_Check
BEFORE INSERT ON LifecycleEvents
FOR EACH ROW
BEGIN
  IF NEW.EventType = 'Disposed' THEN
    IF NOT EXISTS (
      SELECT 1 FROM LifecycleEvents
      WHERE InstanceID = NEW.InstanceID
        AND EventType = 'Sold'
    ) THEN
      SIGNAL SQLSTATE '45000'
      SET MESSAGE_TEXT = 'Cannot dispose unsold product';
    END IF;
  END IF;
END //

/* Hazardous material limit */
CREATE TRIGGER Before_Hazardous_Material
BEFORE INSERT ON ComponentComposition
FOR EACH ROW
BEGIN
  DECLARE haz BOOLEAN;
  SELECT IsHazardous INTO haz
  FROM RawMaterials WHERE MaterialID = NEW.MaterialID;

  IF haz = TRUE AND NEW.WeightInGrams > 500 THEN
    SIGNAL SQLSTATE '45000'
    SET MESSAGE_TEXT = 'Excessive hazardous material use detected!';
  END IF;
END //

/* Backup lifecycle before deletion */
CREATE TRIGGER Before_Lifecycle_Delete
BEFORE DELETE ON LifecycleEvents
FOR EACH ROW
BEGIN
  INSERT INTO LifecycleBackup
  SELECT * FROM LifecycleEvents WHERE EventID = OLD.EventID;
END //

DELIMITER ;
