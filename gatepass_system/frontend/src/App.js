import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import StudentForm from "./components/StudentForm";
import ApproveGatepass from "./components/ApproveGatepass";

function App() {
  return (
    <Router>
      <nav style={{ margin: "20px" }}>
        <Link to="/" style={{ marginRight: "10px" }}>Student</Link>
        <Link to="/parent">Parent</Link>
      </nav>
      <Routes>
        <Route path="/" element={<StudentForm />} />
        <Route path="/parent" element={<ApproveGatepass />} />
      </Routes>
    </Router>
  );
}

export default App;
