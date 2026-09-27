import { useCallback, useRef, useState } from "react";

import api from "../../services/api";
import type {
    Robot,
    RobotLibraryDependency,
    RobotReleaseVersion,
    RobotVersionsResponse,
} from "../../types/robots";
import { obterMensagemErro } from "../../utils/robotErrors";


export function useRobotVersions() {
    const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null);
    const [versions, setVersions] = useState<RobotReleaseVersion[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [downloadingVersion, setDownloadingVersion] = useState<number | null>(null);
    const [expandedVersion, setExpandedVersion] = useState<number | null>(null);
    const [loadingLibraries, setLoadingLibraries] = useState<number | null>(null);
    const [librariesByVersion, setLibrariesByVersion] = useState<Record<number, RobotLibraryDependency[]>>({});
    const requestSequence = useRef(0);

    const loadVersions = useCallback(async (robot: Robot) => {
        const sequence = ++requestSequence.current;
        setSelectedRobot(robot);
        setVersions([]);
        setExpandedVersion(null);
        setLibrariesByVersion({});
        setError("");
        setLoading(true);

        try {
            const response = await api.get<RobotVersionsResponse>(`/robots/${robot.id}/versions`);
            if (sequence !== requestSequence.current) return;
            setVersions(response.data.versions ?? []);
        } catch (requestError) {
            if (sequence !== requestSequence.current) return;
            setError(obterMensagemErro(
                requestError,
                `Não foi possível carregar o histórico de versões de "${robot.name}".`,
            ));
        } finally {
            if (sequence === requestSequence.current) setLoading(false);
        }
    }, []);

    const close = useCallback(() => {
        requestSequence.current += 1;
        setSelectedRobot(null);
        setVersions([]);
        setError("");
        setLoading(false);
        setDownloadingVersion(null);
        setExpandedVersion(null);
        setLoadingLibraries(null);
        setLibrariesByVersion({});
    }, []);

    const downloadVersion = useCallback(async (version: RobotReleaseVersion) => {
        if (!selectedRobot || downloadingVersion !== null) return;
        setDownloadingVersion(version.version);
        setError("");

        try {
            const response = await api.get(
                `/robots/${selectedRobot.id}/versions/${version.version}/download`,
                { responseType: "blob" },
            );
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");
            link.href = url;
            link.download = version.filename;
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(url);
        } catch (requestError) {
            setError(obterMensagemErro(
                requestError,
                `A versão v${version.version} não pôde ser baixada. O servidor verificou o artefato e pode ter encontrado uma inconsistência.`,
            ));
        } finally {
            setDownloadingVersion(null);
        }
    }, [downloadingVersion, selectedRobot]);

    const toggleLibraries = useCallback(async (version: RobotReleaseVersion) => {
        if (!selectedRobot) return;
        if (expandedVersion === version.version) {
            setExpandedVersion(null);
            return;
        }

        setExpandedVersion(version.version);
        if (librariesByVersion[version.version]) return;

        setLoadingLibraries(version.version);
        setError("");
        try {
            const response = await api.get(
                `/robots/${selectedRobot.id}/versions/${version.version}/libraries`,
            );
            setLibrariesByVersion((current) => ({
                ...current,
                [version.version]: response.data?.libraries ?? [],
            }));
        } catch (requestError) {
            setExpandedVersion(null);
            setError(obterMensagemErro(
                requestError,
                `Não foi possível consultar as bibliotecas da versão v${version.version}.`,
            ));
        } finally {
            setLoadingLibraries(null);
        }
    }, [expandedVersion, librariesByVersion, selectedRobot]);

    return {
        selectedRobot,
        versions,
        loading,
        error,
        downloadingVersion,
        expandedVersion,
        loadingLibraries,
        librariesByVersion,
        open: loadVersions,
        retry: selectedRobot ? () => loadVersions(selectedRobot) : undefined,
        close,
        downloadVersion,
        toggleLibraries,
    };
}
