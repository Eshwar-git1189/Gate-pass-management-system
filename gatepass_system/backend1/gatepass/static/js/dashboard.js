// Utility functions
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

function formatDateTime(dateString) {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return date.toLocaleString();
}

// Dashboard updating functions
class DashboardUpdater {
  constructor(updateInterval = 30000) {
    // 30 seconds default
    this.updateInterval = updateInterval;
    this.intervalId = null;
  }

  startAutoUpdate() {
    this.updateDashboard();
    this.intervalId = setInterval(
      () => this.updateDashboard(),
      this.updateInterval
    );
  }

  stopAutoUpdate() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }

  async updateDashboard() {
    // Override in child classes
  }
}

// Warden Dashboard
class WardenDashboardUpdater extends DashboardUpdater {
  async updateDashboard() {
    try {
      const response = await fetch("/api/warden/gatepasses/");
      const data = await response.json();

      // Update stats
      document.getElementById("pendingCount").textContent = data.stats.pending;
      document.getElementById("approvedCount").textContent =
        data.stats.approved;
      document.getElementById("rejectedCount").textContent =
        data.stats.rejected;
      document.getElementById("activeCount").textContent = data.stats.active;

      // Update table
      this.updateGatepassTable(data.gatepasses);
    } catch (error) {
      console.error("Error updating warden dashboard:", error);
    }
  }

  updateGatepassTable(gatepasses) {
    const tbody = document.getElementById("gatepassTable");
    tbody.innerHTML = gatepasses
      .map(
        (gatepass) => `
            <tr class="gatepass-row ${gatepass.status.toLowerCase()}">
                <td>${gatepass.id}</td>
                <td>
                    ${gatepass.student.user.full_name}<br>
                    <small class="text-muted">${
                      gatepass.student.registration_number
                    }</small>
                </td>
                <td>${gatepass.purpose}</td>
                <td>
                    ${formatDateTime(gatepass.request_date)}
                </td>
                <td>
                    <span class="badge bg-${this.getStatusColor(
                      gatepass.status
                    )}">
                        ${gatepass.status}
                    </span>
                </td>
                <td>
                    ${
                      gatepass.parent_response
                        ? '<span class="text-success">Responded</span>'
                        : '<span class="text-warning">Pending</span>'
                    }
                </td>
                <td>
                    ${this.getActionButtons(gatepass)}
                </td>
            </tr>
        `
      )
      .join("");
  }

  getStatusColor(status) {
    switch (status) {
      case "PENDING":
        return "warning";
      case "APPROVED":
        return "success";
      case "REJECTED":
        return "danger";
      default:
        return "secondary";
    }
  }

  getActionButtons(gatepass) {
    let buttons = "";
    if (gatepass.status === "PENDING") {
      buttons += `
                <button class="btn btn-sm btn-success" onclick="approveGatepass('${gatepass.id}')">
                    Approve
                </button>
                <button class="btn btn-sm btn-danger" onclick="rejectGatepass('${gatepass.id}')">
                    Reject
                </button>
            `;
    }
    buttons += `
            <button class="btn btn-sm btn-info" onclick="viewDetails('${gatepass.id}')">
                Details
            </button>
        `;
    return buttons;
  }
}

// Security Dashboard
class SecurityDashboardUpdater extends DashboardUpdater {
  async updateDashboard() {
    try {
      const response = await fetch("/api/security/active-gatepasses/");
      const data = await response.json();

      // Update stats
      document.getElementById("studentsOut").textContent =
        data.stats.students_out;
      document.getElementById("expectedReturns").textContent =
        data.stats.expected_returns;
      document.getElementById("pendingVerifications").textContent =
        data.stats.pending_verifications;

      // Update table
      this.updateGatepassTable(data.gatepasses);
    } catch (error) {
      console.error("Error updating security dashboard:", error);
    }
  }

  updateGatepassTable(gatepasses) {
    const tbody = document.getElementById("gatepassTable");
    tbody.innerHTML = gatepasses
      .map(
        (gatepass) => `
            <tr class="gatepass-row ${gatepass.status.toLowerCase()}">
                <td>${gatepass.id}</td>
                <td>
                    ${gatepass.student.user.full_name}<br>
                    <small class="text-muted">${
                      gatepass.student.registration_number
                    }</small>
                </td>
                <td>${gatepass.purpose}</td>
                <td>${formatDateTime(gatepass.exit_time) || "Not exited"}</td>
                <td>${formatDateTime(gatepass.expected_return)}</td>
                <td>
                    <span class="badge bg-${
                      gatepass.status === "OUT" ? "success" : "info"
                    }">
                        ${gatepass.status}
                    </span>
                </td>
                <td>${this.getActionButtons(gatepass)}</td>
            </tr>
        `
      )
      .join("");
  }

  getActionButtons(gatepass) {
    if (!gatepass.exit_time) {
      return `
                <button class="btn btn-sm btn-success" onclick="logExit('${gatepass.id}')">
                    Log Exit
                </button>
            `;
    }
    if (!gatepass.return_time) {
      return `
                <button class="btn btn-sm btn-info" onclick="logReturn('${gatepass.id}')">
                    Log Return
                </button>
            `;
    }
    return `
            <button class="btn btn-sm btn-secondary" onclick="viewDetails('${gatepass.id}')">
                Details
            </button>
        `;
  }
}

// Initialize dashboard updater based on page type
document.addEventListener("DOMContentLoaded", function () {
  let updater;
  if (document.getElementById("wardenDashboard")) {
    updater = new WardenDashboardUpdater();
  } else if (document.getElementById("securityDashboard")) {
    updater = new SecurityDashboardUpdater();
  }

  if (updater) {
    updater.startAutoUpdate();

    // Stop updates when page is hidden
    document.addEventListener("visibilitychange", function () {
      if (document.hidden) {
        updater.stopAutoUpdate();
      } else {
        updater.startAutoUpdate();
      }
    });
  }
});
