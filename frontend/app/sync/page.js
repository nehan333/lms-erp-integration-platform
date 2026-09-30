import SyncPanel from "@/components/SyncPanel";

export default function SyncPage() {
  return (
    <div className="page-title">
      <h1>Moodle Synchronization</h1>
      <p className="subtitle">
        Check the Moodle connection and trigger an ERP → Moodle sync run.
      </p>
      <SyncPanel />
    </div>
  );
}