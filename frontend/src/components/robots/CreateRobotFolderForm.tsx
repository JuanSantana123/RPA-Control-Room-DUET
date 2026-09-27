import type { RobotFolder } from "../../types/robots";
import {
    flattenRobotFolders,
    getRobotFolderPath,
} from "../../utils/robotFolders";
import { FolderEditorDialog } from "../ui/FolderEditorDialog";

interface CreateRobotFolderFormProps {
    folders: RobotFolder[];
    newFolderName: string;
    newFolderParentId: number | null;
    creatingFolder: boolean;
    onFolderNameChange: (value: string) => void;
    onParentChange: (parentId: number | null) => void;
    onCreateFolder: () => void;
    onCancel: () => void;
}

function CreateRobotFolderForm({
    folders,
    newFolderName,
    newFolderParentId,
    creatingFolder,
    onFolderNameChange,
    onParentChange,
    onCreateFolder,
    onCancel,
}: CreateRobotFolderFormProps) {
    const destinationOptions = flattenRobotFolders(folders).map(({ folder, depth }) => ({
        id: folder.id,
        name: folder.name,
        depth,
        path: getRobotFolderPath(folders, folder.id).map((pathFolder) => pathFolder.name),
    }));

    return (
        <FolderEditorDialog
            idPrefix="robot-folder-editor"
            mode="create"
            eyebrow="Organização do catálogo"
            rootLabel="Raiz de Robôs"
            name={newFolderName}
            parentId={newFolderParentId}
            options={destinationOptions}
            busy={creatingFolder}
            placeholder="Ex.: Conciliações"
            onNameChange={onFolderNameChange}
            onParentChange={onParentChange}
            onSubmit={onCreateFolder}
            onCancel={onCancel}
        />
    );
}

export default CreateRobotFolderForm;
