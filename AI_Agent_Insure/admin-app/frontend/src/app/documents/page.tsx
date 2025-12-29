"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { SidebarTrigger } from "@/components/ui/sidebar";
import { Upload, FileText, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { aiAgent, PdfUploadResponse } from "@/lib/ai-agent-client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export default function DocumentsPage() {
  const [file, setFile] = useState<File | null>(null);
  const [collectionName, setCollectionName] = useState("knowledge_base");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<PdfUploadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      if (selectedFile.type !== "application/pdf") {
        setError("Please select a PDF file");
        setFile(null);
        return;
      }
      setFile(selectedFile);
      setError(null);
      setUploadResult(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError("Please select a file to upload");
      return;
    }

    setIsUploading(true);
    setError(null);
    setUploadResult(null);

    try {
      const result = await aiAgent.uploadPdf(file, collectionName || undefined);
      setUploadResult(result);
      setFile(null);
      // Reset file input
      const fileInput = document.getElementById("pdf-file") as HTMLInputElement;
      if (fileInput) {
        fileInput.value = "";
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to upload PDF");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6 p-6">
      <div className="flex items-center gap-2">
        <SidebarTrigger />
        <div>
          <h1 className="text-3xl font-bold">Document Management</h1>
          <p className="text-muted-foreground">
            Upload PDF documents to the knowledge base
          </p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-5 w-5" />
            Upload PDF Document
          </CardTitle>
          <CardDescription>
            Upload a PDF file to be ingested into the ChromaDB vector store. The document will be
            chunked and made searchable for the AI agent.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pdf-file">PDF File</Label>
            <Input
              id="pdf-file"
              type="file"
              accept=".pdf"
              onChange={handleFileChange}
              disabled={isUploading}
            />
            {file && (
              <p className="text-sm text-muted-foreground">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          <div className="space-y-2">
            <Label htmlFor="collection-name">Collection Name (Optional)</Label>
            <Input
              id="collection-name"
              type="text"
              value={collectionName}
              onChange={(e) => setCollectionName(e.target.value)}
              placeholder="knowledge_base"
              disabled={isUploading}
            />
            <p className="text-xs text-muted-foreground">
              Default: knowledge_base
            </p>
          </div>

          <Button
            onClick={handleUpload}
            disabled={!file || isUploading}
            className="w-full"
          >
            {isUploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              <>
                <Upload className="mr-2 h-4 w-4" />
                Upload PDF
              </>
            )}
          </Button>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {uploadResult && (
            <Alert className="border-green-500 bg-green-50">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <AlertTitle className="text-green-800">Upload Successful</AlertTitle>
              <AlertDescription className="text-green-700">
                <div className="mt-2 space-y-1">
                  <p>
                    <strong>File:</strong> {uploadResult.filename}
                  </p>
                  <p>
                    <strong>Chunks Ingested:</strong> {uploadResult.chunks_ingested}
                  </p>
                  <p>
                    <strong>Collection:</strong> {uploadResult.collection}
                  </p>
                  <p className="mt-2">{uploadResult.message}</p>
                </div>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>About PDF Upload</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>
            • PDFs are automatically chunked into ~1000 character segments with 200 character overlap
          </p>
          <p>
            • Documents are embedded and stored in ChromaDB for semantic search
          </p>
          <p>
            • Uploaded documents become immediately searchable by the AI agent
          </p>
          <p>
            • Only PDF files (.pdf) are supported
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

