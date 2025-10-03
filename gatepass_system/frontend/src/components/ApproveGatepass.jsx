import { useEffect, useState } from "react";
import api from "../api";

export default function ApproveGatepass() {
  const [requests, setRequests] = useState([]);

  useEffect(() => {
    fetchRequests();
  }, []);

  const fetchRequests = async () => {
    try {
      const res = await api.get("gatepasses/");
      setRequests(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  const handleUpdate = async (id, status) => {
    try {
      await api.patch(`gatepasses/${id}/`, { status }); // patch only status
      fetchRequests();
    } catch (error) {
      console.error(error);
      alert("Error updating status");
    }
  };

  return (
    <div>
      <h2>Gatepass Requests</h2>
      {requests.length === 0 && <p>No requests found.</p>}
      {requests.map((req) => (
        <div
          key={req.id}
          style={{ border: "1px solid black", margin: "10px", padding: "10px" }}
        >
          <p>Student ID: {req.student}</p>
          <p>Destination: {req.destination}</p>
          <p>Purpose: {req.purpose}</p>
          <p>Status: {req.status}</p>
          {req.status === "Pending" && (
            <>
              <button onClick={() => handleUpdate(req.id, "Approved")}>Approve</button>
              <button onClick={() => handleUpdate(req.id, "Rejected")}>Reject</button>
            </>
          )}
        </div>
      ))}
    </div>
  );
}
