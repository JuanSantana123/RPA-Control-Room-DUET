import { useCallback, useEffect, useRef, useState } from "react";
import api from "../../services/api";
import { getApiErrorMessage } from "../../utils/apiErrors";

export interface AutomationProjectSummary {
  id: number;
  name: string;
  status: "draft" | "modified" | "published" | "unknown";
  updatedAt: string | null;
  hasCheckout: boolean;
}

interface OverviewData {
  projects: AutomationProjectSummary[];
  robotCount: number;
  folderCount: number;
  availableAgentCount: number;
}

interface OverviewAccess {
  canBuild: boolean;
  canUseCatalog: boolean;
  canViewAgents: boolean;
}

interface OverviewState extends OverviewData {
  loading: boolean;
  refreshing: boolean;
  warnings: string[];
  reload: () => void;
}

const emptyData: OverviewData = { projects: [], robotCount: 0, folderCount: 0, availableAgentCount: 0 };

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function readArray(value: unknown, key: string): unknown[] {
  if (!isRecord(value)) return [];
  const collection = value[key];
  return Array.isArray(collection) ? collection : [];
}

function readProject(value: unknown): AutomationProjectSummary | null {
  if (!isRecord(value) || typeof value.id !== "number" || typeof value.name !== "string") return null;
  const status = value.status;
  const normalizedStatus = status === "draft" || status === "modified" || status === "published" ? status : "unknown";
  return {
    id: value.id,
    name: value.name,
    status: normalizedStatus,
    updatedAt: typeof value.updated_at === "string" ? value.updated_at : null,
    hasCheckout: isRecord(value.checkout),
  };
}

export default function useAutomationOverview(access: OverviewAccess): OverviewState {
  const [data, setData] = useState<OverviewData>(emptyData);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [reloadKey, setReloadKey] = useState(0);
  const dataRef = useRef<OverviewData>(emptyData);
  const hasLoaded = useRef(false);
  const reload = useCallback(() => setReloadKey((current) => current + 1), []);

  useEffect(() => {
    const controller = new AbortController();

    const load = async () => {
      if (hasLoaded.current) setRefreshing(true);
      else setLoading(true);
      setWarnings([]);
      const nextData: OverviewData = {
        ...dataRef.current,
        projects: [...dataRef.current.projects],
      };
      const nextWarnings: string[] = [];
      const requests: Promise<void>[] = [];

      if (access.canBuild) {
        requests.push(api.get<unknown>("/development/projects", { signal: controller.signal })
          .then(({ data: responseData }) => {
            nextData.projects = readArray(responseData, "projects")
              .map(readProject)
              .filter((project): project is AutomationProjectSummary => project !== null && project.status !== "published")
              .sort((left, right) => (right.updatedAt ?? "").localeCompare(left.updatedAt ?? ""));
          })
          .catch((error: unknown) => {
            if (!controller.signal.aborted) nextWarnings.push(getApiErrorMessage(error, "Projetos indisponíveis."));
          }));
      }

      if (access.canUseCatalog) {
        requests.push(
          api.get<unknown>("/robots/root", { signal: controller.signal }).then(({ data: responseData }) => {
            nextData.robotCount = readArray(responseData, "robots").length;
          }).catch((error: unknown) => {
            if (!controller.signal.aborted) nextWarnings.push(getApiErrorMessage(error, "Robôs publicados indisponíveis."));
          }),
          api.get<unknown>("/robot-folders", { signal: controller.signal }).then(({ data: responseData }) => {
            nextData.folderCount = readArray(responseData, "folders").length;
          }).catch((error: unknown) => {
            if (!controller.signal.aborted) nextWarnings.push(getApiErrorMessage(error, "Pastas de robôs indisponíveis."));
          }),
        );
      }

      if (access.canViewAgents) {
        requests.push(api.get<unknown>("/agents/execution/available-agents", { signal: controller.signal })
          .then(({ data: responseData }) => {
            nextData.availableAgentCount = readArray(responseData, "agents").length;
          }).catch((error: unknown) => {
            if (!controller.signal.aborted) nextWarnings.push(getApiErrorMessage(error, "Dispositivos de execução indisponíveis."));
          }));
      }

      await Promise.all(requests);
      if (controller.signal.aborted) return;
      dataRef.current = nextData;
      setData(nextData);
      setWarnings([...new Set(nextWarnings)]);
      hasLoaded.current = true;
      setLoading(false);
      setRefreshing(false);
    };

    void load();
    return () => controller.abort();
  }, [access.canBuild, access.canUseCatalog, access.canViewAgents, reloadKey]);

  return { ...data, loading, refreshing, warnings, reload };
}
