import API from '@/api/Api';

// ==========================================================
// Participants
// ==========================================================

export const getParticipants = async (params) => {
    try {
        const response = await API.get('/participants', { params });
        return response.data;
    } catch (error) {
        console.error('Error fetching participants:', error);
        throw error;
    }
};

export const exportParticipants = async (params = {}) => {
    const participants = await getParticipants(params);
    const rows = [
        ["S. No.", "Trainee Name", "Enrollment Id", "Status"],
        ...(Array.isArray(participants)
            ? participants.map((participant, index) => [
                index + 1,
                participant.participant_name,
                participant.enrollment_no,
                participant.status,
            ])
            : []),
    ];

    const csv = rows
        .map((row) =>
            row
                .map((value) => {
                    const text = value == null ? "" : String(value);
                    return /[",\n\r]/.test(text)
                        ? `"${text.replace(/"/g, '""')}"`
                        : text;
                })
                .join(",")
        )
        .join("\r\n");

    return new Blob(["\uFEFF", csv], {
        type: "text/csv;charset=utf-8",
    });
};

export const createParticipant = async (formData) => {
    try {
        const response = await API.post('/participants/', formData, {
            headers: { 'Content-Type': 'multipart/form-data' },
        });
        return response.data;
    } catch (error) {
        console.error('Error creating participant:', error);
        throw error;
    }
};

// ==========================================================
// Filter / form dropdown data
// ==========================================================

export const getStates = async () => {
    try {
        const response = await API.get('/participants/states');
        return response.data;
    } catch (error) {
        console.error('Error fetching states:', error);
        throw error;
    }
};

export const getDistricts = async (stateLgdCode) => {
    try {
        const response = await API.get(`/participants/districts/${stateLgdCode}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching districts:', error);
        throw error;
    }
};

export const getBlocks = async (districtLgdCode) => {
    try {
        const response = await API.get(`/participants/blocks/${districtLgdCode}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching blocks:', error);
        throw error;
    }
};

export const getCentres = async (blockId) => {
    try {
        const response = await API.get(`/participants/centres/${blockId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching centres:', error);
        throw error;
    }
};

export const getAllCentres = async (params = {}) => {
    try {
        const cleanParams = {};
        if (params?.state_id) cleanParams.state_id = params.state_id;
        if (params?.district_id) cleanParams.district_id = params.district_id;

        const response = await API.get('/participants/participants/all-centres', {
            params: cleanParams,
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching centres:', error);
        throw error;
    }
};

export const getBatches = async (centreId) => {
    try {
        const response = await API.get('/participants/participants/batches', {
            params: centreId ? { centre_id: centreId } : {},
        });
        return response.data;
    } catch (error) {
        console.error('Error fetching batches:', error);
        throw error;
    }
};

export const lookupPostalCodes = async (postOfficeName) => {
    const name = String(postOfficeName || "").trim();
    if (!name) return [];

    const response = await fetch(
        `https://api.postalpincode.in/postoffice/${encodeURIComponent(name)}`
    );
    if (!response.ok) {
        throw new Error(`Postal lookup failed with status ${response.status}`);
    }

    const payload = await response.json();
    const offices = Array.isArray(payload?.[0]?.PostOffice)
        ? payload[0].PostOffice
        : [];

    return offices
        .map((office) => ({
            pincode: String(office.Pincode || ""),
            state: String(office.State || ""),
            district: String(office.District || ""),
            name: String(office.Name || ""),
        }))
        .filter((office) => /^\d{6}$/.test(office.pincode));
};

export const getEnrollment = async (batchId) => {
    try {
        const response = await API.get(`/participants/enrollment/${batchId}`);
        return response.data;
    } catch (error) {
        console.error('Error fetching enrollment:', error);
        throw error;
    }
};

// ==========================================================
// Participant Report
// ==========================================================

export const getParticipantReport = async (participantId) => {
    try {
        const response = await API.get(
            `/participants/${participantId}/report`
        );

        return response.data;
    } catch (error) {
        console.error("Error fetching participant report:", error);
        throw error;
    }
};

// ==========================================================
// Manage Modules
// ==========================================================

export const getParticipantModules = async (participantId, languageId = 1) => {
    const response = await API.get(
        `/participants/${participantId}/modules`,
        { params: { language_id: Number(languageId) } }
    );
    return response.data;
};

export const assignModule = async (participantId, moduleId) => {
    const response = await API.post("/participants/assign", {
        participant_id: participantId,
        module_id: moduleId,
    });
    return response.data;
};

export const unassignModule = async (participantId, moduleId) => {
    const response = await API.post("/participants/unassign", {
        participant_id: participantId,
        module_id: moduleId,
    });
    return response.data;
};

// ==========================================================
// Credentials (key) + Time Spent
// ==========================================================

export const getParticipantKeyDetails = async (participantId) => {
    const response = await API.get(
        `/participants/${participantId}/key-details`
    );
    return response.data;
};

export const getParticipantTimeSpent = async (participantId) => {
    const response = await API.get(
        `/participants/${participantId}/time-spent`
    );
    return response.data;
};

// ==========================================================
// Edit / Update participant
// ==========================================================

export const getParticipantEdit = async (participantId) => {
    const response = await API.get(`/participants/${participantId}/edit`);
    return response.data;
};

export const updateParticipant = async (participantId, formData) => {
    const response = await API.put(`/participants/${participantId}`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
};

export const changeParticipantPassword = async (
    participantId,
    newPassword,
    confirmPassword
) => {
    try {
        const formData = new FormData();
        formData.append("new_password", newPassword);
        formData.append("confirm_password", confirmPassword);

        const response = await API.put(
            `/participants/${participantId}/change-password`,
            formData,
            {
                headers: {
                    "Content-Type": "multipart/form-data",
                },
            }
        );

        return response.data;
    } catch (error) {
        console.error("Error changing participant password:", error);
        throw error;
    }
};