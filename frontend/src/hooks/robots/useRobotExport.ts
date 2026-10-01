// ============================================================
// DUET CORE - ROBOTS - EXPORT HOOK
// ============================================================
//
// Responsabilidade:
// - controlar o fluxo do modal global "Exportar pacote";
// - carregar as versões do Robot escolhido;
// - selecionar por padrão o release vigente;
// - exportar exatamente o snapshot imutável selecionado.
//
// Este hook NÃO:
// - renderiza componentes;
// - conhece a árvore de pastas;
// - recria ou recomprime o pacote publicado.
// ============================================================

import {
    useCallback,
    useRef,
    useState,
} from "react";

import {
    downloadRobotVersion,
    listRobotVersions,
} from "../../services/robotPackagesApi";

import type {
    Robot,
    RobotReleaseVersion,
} from "../../types/robots";

import {
    downloadBlob,
} from "../../utils/browserDownload";

import {
    obterMensagemErro,
} from "../../utils/robotErrors";


function buildExportFilename(
    robot: Robot,
    version: RobotReleaseVersion,
): string {
    const baseName = robot.name
        .replace(/\.zip$/i, "")
        .trim() || "robot";

    return `${baseName}_v${version.version}.zip`;
}


export function useRobotExport() {
    const [isOpen, setIsOpen] = useState(false);
    const [selectedRobot, setSelectedRobot] = useState<Robot | null>(null);
    const [versions, setVersions] = useState<RobotReleaseVersion[]>([]);
    const [selectedVersion, setSelectedVersion] = useState<RobotReleaseVersion | null>(null);
    const [loadingVersions, setLoadingVersions] = useState(false);
    const [exporting, setExporting] = useState(false);
    const [error, setError] = useState("");

    // Evita que uma resposta antiga sobrescreva a seleção mais recente
    // quando o usuário troca rapidamente de Robot no modal.
    const requestSequence = useRef(0);


    const selectRobot = useCallback(async (
        robot: Robot | null,
    ) => {
        const sequence = ++requestSequence.current;

        setSelectedRobot(robot);
        setVersions([]);
        setSelectedVersion(null);
        setError("");

        if (!robot) {
            setLoadingVersions(false);
            return;
        }

        setLoadingVersions(true);

        try {
            const robotVersions = await listRobotVersions(robot.id);

            if (sequence !== requestSequence.current) {
                return;
            }

            setVersions(robotVersions);

            // A versão vigente é a escolha mais segura por padrão.
            // Se a API não marcar uma versão como vigente, usamos a
            // primeira devolvida pelo histórico.
            const defaultVersion =
                robotVersions.find((version) => version.is_current) ??
                robotVersions[0] ??
                null;

            setSelectedVersion(defaultVersion);

        } catch (requestError) {
            if (sequence !== requestSequence.current) {
                return;
            }

            setError(obterMensagemErro(
                requestError,
                `Não foi possível carregar as versões de "${robot.name}".`,
            ));

        } finally {
            if (sequence === requestSequence.current) {
                setLoadingVersions(false);
            }
        }
    }, []);


    const open = useCallback((availableRobots: Robot[]) => {
        setIsOpen(true);
        setError("");
        setVersions([]);
        setSelectedVersion(null);

        // Com apenas um Robot na localização, eliminamos uma etapa
        // desnecessária e já carregamos suas versões.
        const onlyRobot =
            availableRobots.length === 1
                ? availableRobots[0]
                : undefined;

        if (onlyRobot) {
            void selectRobot(onlyRobot);
            return;
        }

        setSelectedRobot(null);
        setLoadingVersions(false);
    }, [selectRobot]);


    const close = useCallback(() => {
        requestSequence.current += 1;
        setIsOpen(false);
        setSelectedRobot(null);
        setVersions([]);
        setSelectedVersion(null);
        setLoadingVersions(false);
        setExporting(false);
        setError("");
    }, []);


    const selectVersion = useCallback((versionNumber: number) => {
        const version = versions.find(
            (item) => item.version === versionNumber,
        ) ?? null;

        setSelectedVersion(version);
        setError("");
    }, [versions]);


    const exportSelected = useCallback(async () => {
        if (!selectedRobot || !selectedVersion || exporting) {
            return;
        }

        setExporting(true);
        setError("");

        try {
            const blob = await downloadRobotVersion(
                selectedRobot.id,
                selectedVersion.version,
            );

            downloadBlob(
                blob,
                buildExportFilename(selectedRobot, selectedVersion),
            );

            close();

        } catch (requestError) {
            setError(obterMensagemErro(
                requestError,
                `Não foi possível exportar ${selectedRobot.name} v${selectedVersion.version}. O artefato publicado pode estar indisponível ou inconsistente.`,
            ));

            setExporting(false);
        }
    }, [close, exporting, selectedRobot, selectedVersion]);


    return {
        isOpen,
        selectedRobot,
        versions,
        selectedVersion,
        loadingVersions,
        exporting,
        error,
        open,
        close,
        selectRobot,
        selectVersion,
        exportSelected,
    };
}
