import { useRef, useState } from "react";
import api from "../../services/api";
import type { SystemLog } from "../../types/logs";
import { getApiErrorMessage } from "../../utils/apiErrors";
import { usePollingTask } from "../async/usePollingTask";

interface LogsResponse {
  status: "success" | "error";
  logs?: SystemLog[];
  message?: string;
  total?: number;
  truncated?: boolean;
}

export function useLogsData(autoRefresh = true) {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [total, setTotal] = useState(0);
  const [truncated, setTruncated] = useState(false);
  const requestSequence = useRef(0);

  const carregarLogsComSinal = async (background = false, signal?: AbortSignal) => {
    const requestId = ++requestSequence.current;
    if (background) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    try {
      const response = await api.get<LogsResponse>("/logs", {
        params: { limit: 500 },
        signal,
      });
      if (response.data.status !== "success") throw new Error(response.data.message || "Falha ao consultar os logs.");
      if (requestId !== requestSequence.current) return;
      setLogs(response.data.logs ?? []);
      setTotal(response.data.total ?? response.data.logs?.length ?? 0);
      setTruncated(Boolean(response.data.truncated));
      setLastUpdated(new Date());
      setError("");
    } catch (requestError) {
      if (signal?.aborted || requestId !== requestSequence.current) return;
      setError(getApiErrorMessage(requestError, "Não foi possível atualizar os logs do sistema."));
    } finally {
      if (!signal?.aborted && requestId === requestSequence.current) {
        setLoading(false);
        setRefreshing(false);
      }
    }
  };

  usePollingTask(
    (signal) => carregarLogsComSinal(logs.length > 0, signal),
    { enabled: autoRefresh, intervalMs: 5000 },
  );

  return {
    logs,
    loading,
    refreshing,
    error,
    lastUpdated,
    total,
    truncated,
    carregarLogs: () => carregarLogsComSinal(true),
  };
}
