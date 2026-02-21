import { ClassifiedComplaint } from "@/pages/Index";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AlertCircle, Clock, CheckCircle, Send, Trash2 } from "lucide-react";
import { formatDistanceToNow } from "date-fns";
import { useToast } from "@/hooks/use-toast";
import { useState } from "react";

interface ClassificationResultsProps {
  complaints: ClassifiedComplaint[];
  onEmailSent: () => void;
  onHistoryCleared: () => void;
}

export const ClassificationResults = ({ complaints, onEmailSent, onHistoryCleared }: ClassificationResultsProps) => {
  const { toast } = useToast();
  const [sendingFolder, setSendingFolder] = useState<string | null>(null);
  const [clearingFolder, setClearingFolder] = useState<string | null>(null);
  const [clearingAll, setClearingAll] = useState(false);

  const handleClearFolder = async (priority: string, folderName: string) => {
    setClearingFolder(folderName);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/petitions/clear/${priority}`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to clear folder');

      const data = await response.json();

      toast({
        title: "Folder cleared",
        description: `Cleared ${data.deleted} petition${data.deleted !== 1 ? 's' : ''} from ${folderName} folder`,
      });

      onHistoryCleared();
    } catch (error) {
      console.error("Clear folder error:", error);
      toast({
        title: "Clear failed",
        description: "Failed to clear folder",
        variant: "destructive",
      });
    } finally {
      setClearingFolder(null);
    }
  };

  const handleClearAll = async () => {
    setClearingAll(true);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/petitions/clear-all`, {
        method: 'DELETE',
      });

      if (!response.ok) throw new Error('Failed to clear all');

      const data = await response.json();

      toast({
        title: "All cleared",
        description: `Cleared ${data.deleted} petition${data.deleted !== 1 ? 's' : ''} from history`,
      });

      onHistoryCleared();
    } catch (error) {
      console.error("Clear all error:", error);
      toast({
        title: "Clear failed",
        description: "Failed to clear all petitions",
        variant: "destructive",
      });
    } finally {
      setClearingAll(false);
    }
  };

  const handleSendFolderEmails = async (folderComplaints: ClassifiedComplaint[], folderName: string) => {
    setSendingFolder(folderName);

    try {
      let successCount = 0;
      let failCount = 0;

      for (const complaint of folderComplaints) {
        if (complaint.email_sent) continue;

        try {
          const response = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:5000"}/api/send-email/${complaint.id}`, {
            method: 'POST',
          });

          if (!response.ok) throw new Error('Email failed');

          successCount++;
        } catch (error) {
          console.error(`Email error for ${complaint.fileName}:`, error);
          failCount++;
        }
      }

      if (successCount > 0) {
        toast({
          title: "Emails sent",
          description: `Successfully sent ${successCount} petition${successCount > 1 ? 's' : ''} from ${folderName} folder`,
        });
      }

      if (failCount > 0) {
        toast({
          title: "Some emails failed",
          description: `Failed to send ${failCount} petition${failCount > 1 ? 's' : ''}`,
          variant: "destructive",
        });
      }

      onEmailSent();
    } catch (error) {
      console.error("Folder email error:", error);
      toast({
        title: "Email failed",
        description: "Failed to send folder emails",
        variant: "destructive",
      });
    } finally {
      setSendingFolder(null);
    }
  };

  const getPriorityIcon = (priority: ClassifiedComplaint["priority"]) => {
    switch (priority) {
      case "urgent":
        return <AlertCircle className="w-4 h-4" />;
      case "neutral":
        return <Clock className="w-4 h-4" />;
      case "later":
        return <CheckCircle className="w-4 h-4" />;
    }
  };

  const getPriorityLabel = (priority: ClassifiedComplaint["priority"]) => {
    switch (priority) {
      case "urgent":
        return "Urgent";
      case "neutral":
        return "Neutral";
      case "later":
        return "Can Do Later";
    }
  };

  const getPriorityColor = (priority: ClassifiedComplaint["priority"]) => {
    switch (priority) {
      case "urgent":
        return "bg-urgent text-urgent-foreground";
      case "neutral":
        return "bg-neutral text-neutral-foreground";
      case "later":
        return "bg-later text-later-foreground";
    }
  };

  // Group complaints by priority (folders)
  const urgentComplaints = complaints.filter(c => c.priority === "urgent");
  const neutralComplaints = complaints.filter(c => c.priority === "neutral");
  const laterComplaints = complaints.filter(c => c.priority === "later");

  const renderComplaintCard = (complaint: ClassifiedComplaint) => (
    <Card key={complaint.id} className="p-6 bg-gradient-card hover:shadow-lg transition-shadow">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-2">
              <Badge className={getPriorityColor(complaint.priority)}>
                <span className="flex items-center gap-1.5">
                  {getPriorityIcon(complaint.priority)}
                  {getPriorityLabel(complaint.priority)}
                </span>
              </Badge>
              <Badge variant="outline" className="capitalize">
                {complaint.department}
              </Badge>
              {complaint.email_sent && (
                <Badge variant="secondary" className="ml-auto">
                  <CheckCircle className="w-3 h-3 mr-1" />
                  Sent
                </Badge>
              )}
            </div>
            <h3 className="text-lg font-semibold text-foreground mb-1 truncate">
              {complaint.fileName}
            </h3>
            <p className="text-sm text-muted-foreground">
              Classified {formatDistanceToNow(complaint.timestamp, { addSuffix: true })}
            </p>
          </div>
        </div>

        {/* Extracted Text */}
        <div className="pt-4 border-t border-border">
          <p className="text-sm font-medium text-foreground mb-2">Extracted Content:</p>
          <p className="text-sm text-muted-foreground leading-relaxed">
            {complaint.text}
          </p>
        </div>
      </div>
    </Card>
  );

  const renderPrioritySection = (title: string, complaints: ClassifiedComplaint[], color: string, priority: string) => {
    if (complaints.length === 0) return null;

    const unsentCount = complaints.filter(c => !c.email_sent).length;

    return (
      <div className="space-y-4">
        <div className="flex items-center gap-3 justify-between">
          <div className="flex items-center gap-3">
            <h3 className={`text-xl font-bold ${color}`}>{title}</h3>
            <Badge variant="secondary">{complaints.length} petition{complaints.length !== 1 ? 's' : ''}</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button
              onClick={() => handleSendFolderEmails(complaints, title)}
              disabled={sendingFolder === title || unsentCount === 0}
              variant="default"
            >
              <Send className="w-4 h-4 mr-2" />
              {sendingFolder === title ? "Sending..." : unsentCount === 0 ? "All Sent" : `Send All (${unsentCount})`}
            </Button>
            <Button
              onClick={() => handleClearFolder(priority, title)}
              disabled={clearingFolder === title}
              variant="destructive"
            >
              {clearingFolder === title ? "Clearing..." : "Clear"}
            </Button>
          </div>
        </div>
        <div className="space-y-4">
          {complaints.map(renderComplaintCard)}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-8">
      {complaints.length > 0 && (
        <div className="flex justify-end">
          <Button
            onClick={handleClearAll}
            disabled={clearingAll}
            variant="destructive"
            size="lg"
          >
            {clearingAll ? "Clearing All..." : "Clear All History"}
          </Button>
        </div>
      )}

      {renderPrioritySection("🔴 Urgent Folder", urgentComplaints, "text-urgent", "urgent")}
      {renderPrioritySection("🟡 Neutral Folder", neutralComplaints, "text-neutral", "neutral")}
      {renderPrioritySection("🟢 Later Folder", laterComplaints, "text-later", "later")}

      {complaints.length === 0 && (
        <Card className="p-6 bg-gradient-card">
          <p className="text-center text-muted-foreground">No petitions classified yet</p>
        </Card>
      )}
    </div>
  );
};
