export const getDocuments = async () => {
  const token = localStorage.getItem("token");

  const response = await axios.get(
    `${API_BASE_URL}/documents`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );

  return response.data;
};

export const deleteDocument = async (id) => {
  const token = localStorage.getItem("token");

  return axios.delete(
    `${API_BASE_URL}/documents/${id}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
};