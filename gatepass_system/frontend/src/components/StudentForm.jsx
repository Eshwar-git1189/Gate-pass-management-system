import { useState } from "react";
import api from "../api";

export default function StudentForm() {
  const [studentId, setStudentId] = useState("");
  const [destination, setDestination] = useState("");
  const [purpose, setPurpose] = useState("");
  const [dateTime, setDateTime] = useState("");
  const [duration, setDuration] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      await api.post("gatepasses/", {
        student: parseInt(studentId, 10),   // ✅ convert to integer
        destination,
        purpose,
        date_time: new Date(dateTime).toISOString(), // ✅ convert to ISO format
        duration: parseInt(duration, 10),   // ✅ convert to integer
        status: "Pending",
      });

      alert("Gatepass requested successfully!");

      // reset form
      setStudentId("");
      setDestination("");
      setPurpose("");
      setDateTime("");
      setDuration("");
    } catch (error) {
      console.error("❌ API error:", error.response?.data || error.message);
      alert("Error submitting gatepass. Check console for details.");
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Request Gatepass</h2>

      <input
        type="number"
        placeholder="Student ID"
        value={studentId}
        onChange={(e) => setStudentId(e.target.value)}
        required
      />

      <input
        type="text"
        placeholder="Destination"
        value={destination}
        onChange={(e) => setDestination(e.target.value)}
        required
      />

      <input
        type="text"
        placeholder="Purpose"
        value={purpose}
        onChange={(e) => setPurpose(e.target.value)}
        required
      />

      <input
        type="datetime-local"
        value={dateTime}
        onChange={(e) => setDateTime(e.target.value)}
        required
      />

      <input
        type="number"
        placeholder="Duration (hours)"
        value={duration}
        onChange={(e) => setDuration(e.target.value)}
        required
      />

      <button type="submit">Request Gatepass</button>
    </form>
  );
}
