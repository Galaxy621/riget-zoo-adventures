CREATE TABLE `hotels` (
  `RoomID` int(11) NOT NULL,
  `Name` varchar(32) NOT NULL,
  `Description` varchar(512) NOT NULL,
  `MaxOccupants` int(11) NOT NULL,
  `Cost` int(11) NOT NULL,

  PRIMARY KEY (`RoomID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `users` (
  `UserID` int(11) NOT NULL,
  `Name` varchar(32) NOT NULL,
  `Email` varchar(256) NOT NULL,
  `DateOfBirth` date NOT NULL,
  `Admin` tinyint(1) NOT NULL,
  `IsStudent` tinyint(1) NOT NULL,
  `IsCarer` tinyint(1) NOT NULL,
  `PasswordHash` char(64) NOT NULL,
  `PasswordSalt` char(16) NOT NULL,

  PRIMARY KEY (`UserID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE `posts` (
  `PostID` int(11) NOT NULL,
  `AuthorID` int(11) NOT NULL,
  `CreationTime` datetime NOT NULL DEFAULT current_timestamp(),
  `Title` varchar(64) NOT NULL,
  `Contents` varchar(4096) NOT NULL,
  `Unlisted` tinyint(1) NOT NULL,

  PRIMARY KEY (`PostID`),
  KEY `Author` (`AuthorID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;


CREATE TABLE `bookings` (
  `BookingID` int(11) NOT NULL,
  `UserID` int(11) NOT NULL,
  `RoomID` int(11) NOT NULL,
  `Occupants` int(11) NOT NULL,
  `Cost` int(11) NOT NULL,
  `PurchasedAt` datetime NOT NULL DEFAULT current_timestamp(),
  `StartDate` datetime DEFAULT NULL,
  `EndDate` datetime DEFAULT NULL,

  PRIMARY KEY (`BookingID`),
  KEY `room` (`RoomID`),
  KEY `user` (`UserID`)

) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

ALTER TABLE `posts`
  ADD CONSTRAINT `Author` FOREIGN KEY (`AuthorID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

ALTER TABLE `bookings`
  ADD CONSTRAINT `room` FOREIGN KEY (`RoomID`) REFERENCES `hotels` (`RoomID`) ON DELETE CASCADE ON UPDATE CASCADE,
  ADD CONSTRAINT `user` FOREIGN KEY (`UserID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE ON UPDATE CASCADE;
COMMIT;

INSERT INTO `hotels` (`RoomID`, `Name`, `Description`, `MaxOccupants`, `Cost`) VALUES (-1, 'Safari Experience', 'Safari Experience', 0, 0);