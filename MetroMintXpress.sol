// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";

/**
 * @title MetroMintXpress
 * @notice A smart contract for creating and verifying NFT-based metro tickets on BNB Chain.
 */
contract MetroMintXpress is ERC721, Ownable {
    using Counters for Counters.Counter;
    Counters.Counter private _tokenIds;

    struct TicketInfo {
        string origin;
        string destination;
        uint256 purchaseTimestamp;
        bool isUsed;
    }

    mapping(uint256 => TicketInfo) public ticketDetails;

    event TicketUsed(uint256 indexed tokenId);

    constructor() ERC721("MetroMint Xpress Ticket", "MMT") {}

    function mintTicket(address _to, string memory _origin, string memory _destination)
        public
        onlyOwner
        returns (uint256)
    {
        _tokenIds.increment();
        uint256 newItemId = _tokenIds.current();
        _safeMint(_to, newItemId);

        ticketDetails[newItemId] = TicketInfo({
            origin: _origin,
            destination: _destination,
            purchaseTimestamp: block.timestamp,
            isUsed: false
        });

        return newItemId;
    }

    function isTicketValid(uint256 _tokenId) public view returns (bool) {
        return _exists(_tokenId) && !ticketDetails[_tokenId].isUsed;
    }

    function useTicket(uint256 _tokenId) public onlyOwner {
        require(isTicketValid(_tokenId), "MetroMint: Ticket is invalid or already used.");
        ticketDetails[_tokenId].isUsed = true;
        emit TicketUsed(_tokenId);
    }
    
    function _baseURI() internal pure override returns (string memory) {
        return "https://api.metromint.xpress/tickets/"; // Example API endpoint
    }
}