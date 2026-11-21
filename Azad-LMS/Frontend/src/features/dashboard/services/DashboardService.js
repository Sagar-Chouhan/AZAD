import API from "@/api/Api";

const cleanParams = (params = {}) =>
    Object.fromEntries(
        Object.entries(params).filter(
            ([, value]) =>
                value !== "" &&
                value !== null &&
                value !== undefined
        )
    );

/* ============================
   Dashboard Summary
============================ */

export const getDashboardSummary = async (filters = {}) => {
    const response = await API.get("/dashboard", {
        params: cleanParams(filters),
    });

    return response.data;
};

/* ============================
   Trainee Status (detail list)
============================ */

export const getTraineeStatusDetails = async (filters = {}) => {
    const response = await API.get("/dashboard/trainee-status/details", {
        params: cleanParams(filters),
    });

    return response.data;
};

export const getStateWiseTraineeStatus = async (filters = {}) => {
    const response = await API.get(
        "/dashboard/state-wise-trainee-status",
        { params: cleanParams(filters) }
    );

    return response.data;
};

export const getMonthlyTrendingModules = async (filters = {}) => {
    const response = await API.get(
        "/dashboard/monthly-trending-modules",
        { params: cleanParams(filters) }
    );

    return response.data;
};

export const getModuleAssignmentUsage = async (filters = {}) => {
    const response = await API.get(
        "/dashboard/module-assignment-usage",
        { params: cleanParams(filters) }
    );

    return response.data;
};

/* ============================
   State Wise Participants
============================ */

export const getStateWiseParticipants = async (filters = {}) => {
    const response = await API.get(
        "/dashboard/state-wise-participants",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   District Wise Participants
============================ */

export const getDistrictWiseParticipants = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/district-wise-participants",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Gender Distribution
============================ */

export const getGenderDistribution = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/gender-distribution",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Age Group Distribution
============================ */

export const getAgeGroupDistribution = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/age-group-distribution",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   State Wise Centres
============================ */

export const getStateWiseCentres = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/state-wise-centres",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Module Performance
============================ */

export const getModulePerformance = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/module-wise-performance",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Document Distribution
============================ */

export const getDocumentDistribution = async () => {
    const response = await API.get(
        "/dashboard/document-type-distribution"
    );

    return response.data;
};

/* ============================
   Monthly Logins
============================ */

export const getMonthlyLogins = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/monthly-logins",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Monthly Login Details
============================ */

export const getMonthlyLoginDetails = async (
    filters = {}
) => {
    const response = await API.get(
        "/dashboard/monthly-logins/details",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

/* ============================
   Centre Wise Trainees
============================ */
export const getCentreWiseTrainees = async (filters = {}) => {
    const response = await API.get(
        "/dashboard/centre-wise-trainees",
        {
            params: cleanParams(filters),
        }
    );

    return response.data;
};

export const getStateWiseTrainees = async (filters = {}) => {
    const params = {};

    if (filters.state_id != null && filters.state_id !== "") {
        params.state_id = filters.state_id;
    }

    if (filters.district_id != null && filters.district_id !== "") {
        params.district_id = filters.district_id;
    }

    if (filters.centre_id != null && filters.centre_id !== "") {
        params.centre_id = filters.centre_id;
    }

    if (filters.from_date) {
        params.from_date = filters.from_date;
    }

    if (filters.to_date) {
        params.to_date = filters.to_date;
    }

    const response = await API.get("/dashboard/state-wise-trainees", {
        params,
    });

    const result = response.data;

    if (Array.isArray(result)) return result;
    if (Array.isArray(result?.data)) return result.data;

    return [];
};

/* ============================
   Need Attention & Recent / Top Learners
============================ */

export const getNeedAttentionSummary = async (filters = {}) => {
    const response = await API.get("/dashboard/need-attention", {
        params: cleanParams(filters),
    });
    return response.data;
};

export const getNeedAttentionLearners = async (filters = {}) => {
    const response = await API.get("/dashboard/need-attention/learners", {
        params: cleanParams(filters),
    });
    return response.data;
};

export const getRecentLearners = async (filters = {}) => {
    const response = await API.get("/dashboard/recent-learners", {
        params: cleanParams(filters),
    });
    return response.data;
};

export const getTopLearners = async (filters = {}) => {
    try {
        const response = await API.get("/dashboard/top-learners", {
            params: cleanParams(filters),
        });
        return response.data;
    } catch {
        return null;
    }
};

export const getLearnerActivityDetail = async (participantId) => {
    const response = await API.get(`/dashboard/recent-learners/${participantId}`);
    return response.data;
};

export const getParticipantTimeSpent = async (participantId) => {
    try {
        const response = await API.get(`/participants/${participantId}/time-spent`);
        return response.data;
    } catch {
        return null;
    }
};

export const exportNeedAttentionLearners = async (filters = {}) => {
    const response = await API.get("/dashboard/need-attention/export", {
        params: cleanParams(filters),
        responseType: "blob",
    });
    return response.data;
};

export const getCentreLeaderboard = async (filters = {}) => {
    const response = await API.get("/dashboard/centre-leaderboard", {
        params: cleanParams(filters),
    });
    return response.data;
};
