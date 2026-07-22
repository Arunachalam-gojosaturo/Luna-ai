import React, { useState, useEffect } from "react";
import { 
  GitBranch, GitCommit, GitPullRequest, AlertCircle, RefreshCw, 
  Star, GitFork, ExternalLink, Key, Check, BookOpen 
} from "lucide-react";

interface GithubMonitorProps {
  token: string;
  onUpdateToken: (token: string) => void;
  isLight?: boolean;
}

interface Repo {
  name: string;
  full_name: string;
  description: string;
  stars: number;
  forks: number;
  open_issues_count: number;
  branch: string;
  url: string;
}

interface Commit {
  sha: string;
  message: string;
  author: string;
  date: string;
}

interface Issue {
  number: number;
  title: string;
  user: string;
  created_at: string;
}

interface RepoDetails {
  commits: Commit[];
  open_issues_count: number;
  open_prs_count: number;
  recent_issues: Issue[];
}

interface UserProfile {
  login: string;
  avatar_url: string;
  name: string;
  html_url: string;
  bio: string;
  followers: number;
  following: number;
  public_repos: number;
}

interface Contributor {
  login: string;
  contributions: number;
  avatar_url: string;
}

interface Release {
  tag_name: string;
  name: string;
  published_at: string;
  html_url: string;
}

interface WorkflowRun {
  id: number;
  name: string;
  status: string;
  conclusion: string;
  event: string;
  html_url: string;
  commit_message: string;
}

interface ExtendedDetails {
  contributors: Contributor[];
  releases: Release[];
  workflow_runs: WorkflowRun[];
}

export default function GithubMonitor({
  token,
  onUpdateToken,
  isLight = false
}: GithubMonitorProps) {
  const [inputToken, setInputToken] = useState(token);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repo | null>(null);
  const [details, setDetails] = useState<RepoDetails | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [extendedDetails, setExtendedDetails] = useState<ExtendedDetails | null>(null);
  const [loading, setLoading] = useState(false);
  const [detailsLoading, setDetailsLoading] = useState(false);
  const [profileLoading, setProfileLoading] = useState(false);
  const [extendedLoading, setExtendedLoading] = useState(false);
  const [showExtended, setShowExtended] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchRepos = async (authToken: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`http://localhost:3000/api/agents/github/repos?token=${encodeURIComponent(authToken)}`);
      const data = await response.json();
      if (data.status === "success") {
        setRepos(data.repos);
        if (data.repos.length > 0) {
          setSelectedRepo(data.repos[0]);
        }
      } else {
        setError(data.message || "Failed to retrieve repositories");
      }
    } catch (e: any) {
      setError(e.message || "Network error occurred");
    } finally {
      setLoading(false);
    }
  };

  const fetchUserProfile = async (authToken: string) => {
    setProfileLoading(true);
    try {
      const response = await fetch(`http://localhost:3000/api/agents/github/profile?token=${encodeURIComponent(authToken)}`);
      const data = await response.json();
      if (data.status === "success") {
        setProfile(data.profile);
      } else {
        console.error("Failed to load profile:", data.message);
      }
    } catch (e) {
      console.error("Error loading profile:", e);
    } finally {
      setProfileLoading(false);
    }
  };

  const fetchRepoDetails = async (repo: Repo) => {
    setDetailsLoading(true);
    const [owner, repoName] = repo.full_name.split("/");
    try {
      const response = await fetch(
        `http://localhost:3000/api/agents/github/repo_details?token=${encodeURIComponent(token)}&owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repoName)}`
      );
      const data = await response.json();
      if (data.status === "success") {
        setDetails(data.details);
      } else {
        console.error("Failed to load details:", data.message);
      }
    } catch (e) {
      console.error("Error loading details:", e);
    } finally {
      setDetailsLoading(false);
    }
  };

  const fetchExtendedRepoDetails = async () => {
    if (!selectedRepo) return;
    setExtendedLoading(true);
    const [owner, repoName] = selectedRepo.full_name.split("/");
    try {
      const response = await fetch(
        `http://localhost:3000/api/agents/github/repo_extended?token=${encodeURIComponent(token)}&owner=${encodeURIComponent(owner)}&repo=${encodeURIComponent(repoName)}`
      );
      const data = await response.json();
      if (data.status === "success") {
        setExtendedDetails(data.extended);
        setShowExtended(true);
      } else {
        console.error("Failed to load extended details:", data.message);
      }
    } catch (e) {
      console.error("Error loading extended details:", e);
    } finally {
      setExtendedLoading(false);
    }
  };

  useEffect(() => {
    if (token) {
      fetchRepos(token);
      fetchUserProfile(token);
    } else {
      setProfile(null);
    }
  }, [token]);

  useEffect(() => {
    if (selectedRepo) {
      fetchRepoDetails(selectedRepo);
      setExtendedDetails(null);
      setShowExtended(false);
    }
  }, [selectedRepo]);

  const handleConnect = () => {
    if (inputToken.trim()) {
      onUpdateToken(inputToken.trim());
    }
  };

  const handleDisconnect = () => {
    onUpdateToken("");
    setInputToken("");
    setRepos([]);
    setSelectedRepo(null);
    setDetails(null);
    setProfile(null);
  };

  if (!token) {
    return (
      <div className={`p-8 rounded-3xl border text-center max-w-lg mx-auto backdrop-blur-md ${
        isLight ? 'bg-white/40 border-slate-200' : 'bg-slate-950/60 border-slate-900'
      }`}>
        <div className="w-12 h-12 bg-cyan-500/10 border border-cyan-500/20 text-cyan-500 rounded-full flex items-center justify-center mx-auto mb-4">
          <BookOpen className="w-6 h-6" />
        </div>
        <h3 className={`text-md font-bold font-display ${isLight ? 'text-slate-900' : 'text-white'}`}>Connect GitHub Monitor</h3>
        <p className={`text-xs mt-2 mb-6 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
          Enter a Personal Access Token (PAT) with <code>repo</code> permissions to track real repository activity, commit feeds, issues, and pull requests.
        </p>
        <div className="flex flex-col gap-3">
          <div className="relative">
            <input
              type="password"
              placeholder="github_pat_..."
              value={inputToken}
              onChange={(e) => setInputToken(e.target.value)}
              className={`w-full text-xs p-3 pr-10 rounded-xl border outline-none font-mono focus:border-cyan-500 transition-all ${
                isLight 
                  ? 'bg-white border-slate-200 text-slate-800' 
                  : 'bg-slate-900 border-slate-800 text-slate-200'
              }`}
            />
            <Key className="w-4 h-4 text-slate-500 absolute right-3.5 top-1/2 -translate-y-1/2" />
          </div>
          <button
            onClick={handleConnect}
            className="w-full py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-xs font-bold font-mono tracking-wider transition-all shadow-lg shadow-cyan-600/25"
          >
            CONNECT REPOSITORY MONITOR
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6 w-full h-full">
      {profile && (
        <div className={`p-5 rounded-3xl border backdrop-blur-md flex flex-col md:flex-row md:items-center justify-between gap-6 transition-all duration-300 ${
          isLight 
            ? "bg-white/40 border-white/60 shadow-md text-slate-800" 
            : "bg-slate-950/60 border border-slate-900 text-slate-100"
        }`}>
          <div className="flex items-center gap-4">
            <div className="relative shrink-0">
              <div className="absolute -inset-0.5 bg-gradient-to-r from-cyan-500 to-indigo-500 rounded-full blur opacity-50"></div>
              <img 
                src={profile.avatar_url} 
                alt={profile.name} 
                className="relative w-14 h-14 rounded-full border-2 border-cyan-400 object-cover shadow-lg"
              />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h1 className={`text-base font-bold font-display ${isLight ? "text-slate-900" : "text-white"}`}>{profile.name}</h1>
                <a href={profile.html_url} target="_blank" rel="noopener noreferrer" className="text-xs font-mono text-cyan-450 hover:underline">
                  @{profile.login}
                </a>
              </div>
              <p className={`text-xs mt-1 max-w-xl line-clamp-2 ${isLight ? "text-slate-500" : "text-slate-400"}`}>
                {profile.bio || "No biography provided."}
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-5 self-end md:self-auto font-mono text-xs text-slate-400 border-t md:border-t-0 md:border-l border-slate-200/10 pt-3 md:pt-0 md:pl-5 shrink-0">
            <div className="flex flex-col items-center">
              <span className={`text-sm font-bold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>{profile.public_repos}</span>
              <span className="text-[9px] text-slate-500">REPOSITORIES</span>
            </div>
            <div className="flex flex-col items-center">
              <span className={`text-sm font-bold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>{profile.followers}</span>
              <span className="text-[9px] text-slate-500">FOLLOWERS</span>
            </div>
            <div className="flex flex-col items-center">
              <span className={`text-sm font-bold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>{profile.following}</span>
              <span className="text-[9px] text-slate-500">FOLLOWING</span>
            </div>
          </div>
        </div>
      )}

      <div className={`grid grid-cols-1 lg:grid-cols-3 gap-6 h-full flex-1 ${isLight ? 'text-slate-800' : 'text-slate-100'}`}>
        
        {/* Repositories Sidebar List */}
        <div className="lg:col-span-1 flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <h2 className={`text-sm font-bold font-display flex items-center gap-2 ${isLight ? 'text-slate-900' : 'text-white'}`}>
              <BookOpen className="w-4 h-4 text-cyan-500" />
              GitHub Repositories
            </h2>
            <button 
              onClick={() => fetchRepos(token)}
              disabled={loading}
              className="p-1.5 text-slate-400 hover:text-cyan-400 border border-transparent hover:border-slate-800 rounded-lg transition-all"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {error && (
            <div className="p-3 border rounded-xl border-rose-900/30 bg-rose-950/15 text-rose-400 text-xs flex gap-2 items-center">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-3 overflow-y-auto flex-1 pr-1 max-h-[500px]">
            {loading ? (
              <div className="py-12 text-center text-xs text-slate-500 font-mono">
                Fetching repositories from GitHub...
              </div>
            ) : repos.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500 font-mono">
                No repositories found.
              </div>
            ) : (
              repos.map((repo) => {
                const isSelected = selectedRepo?.full_name === repo.full_name;
                return (
                  <div
                    key={repo.full_name}
                    onClick={() => setSelectedRepo(repo)}
                    className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer flex flex-col gap-2 relative ${
                      isSelected 
                        ? (isLight ? 'bg-white/70 border-cyan-200 shadow-md' : 'bg-slate-900/60 border-slate-800 shadow-lg shadow-black/10')
                        : (isLight ? 'bg-white/30 border-slate-200 hover:bg-white/50' : 'bg-slate-950/40 border-slate-900/60 hover:bg-slate-900/30')
                    }`}
                  >
                    {isSelected && (
                      <div className="absolute inset-y-4 left-0 w-1 bg-cyan-400 rounded-r-md" />
                    )}
                    <div className="flex items-center justify-between">
                      <h3 className={`text-xs font-bold truncate max-w-[170px] ${isLight ? 'text-slate-800' : 'text-white'}`}>{repo.name}</h3>
                      <div className="flex items-center gap-2 text-[10px] text-slate-400 font-mono">
                        <span className="flex items-center gap-0.5"><Star className="w-3 h-3 text-amber-500 fill-amber-500/20" /> {repo.stars}</span>
                      </div>
                    </div>
                    <p className="text-[10px] text-slate-400 line-clamp-2 leading-relaxed">{repo.description}</p>
                  </div>
                );
              })
            )}
          </div>

          <button
            onClick={handleDisconnect}
            className={`w-full mt-2 py-2 border rounded-xl text-[10px] font-bold font-mono tracking-wider transition-all ${
              isLight
                ? 'bg-rose-50 hover:bg-rose-100 border-rose-200 text-rose-700'
                : 'bg-rose-950/20 hover:bg-rose-900/20 border-rose-900/40 text-rose-400'
            }`}
          >
            DISCONNECT GITHUB
          </button>
        </div>

        {/* Selected Repository Analytics Detail Panel */}
        <div className={`lg:col-span-2 border rounded-2xl p-6 backdrop-blur-md relative overflow-hidden flex flex-col justify-between ${
          isLight ? 'bg-white/60 border-slate-200/60 shadow-lg' : 'bg-slate-950/60 border-slate-900'
        }`}>
          {selectedRepo ? (
            <div className="space-y-6 flex-1 flex flex-col justify-between">
              {/* Header info */}
              <div className="flex justify-between items-start border-b border-slate-200/10 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className={`text-base font-bold font-display ${isLight ? 'text-slate-900' : 'text-white'}`}>{selectedRepo.name}</h2>
                    <a href={selectedRepo.url} target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-cyan-400">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                  <p className="text-[10px] font-mono text-slate-400 mt-1 uppercase">Full Name: {selectedRepo.full_name}</p>
                </div>

                <div className="flex gap-2">
                  <span className="text-[10px] font-mono border border-slate-800 bg-slate-950/40 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                    <GitBranch className="w-3.5 h-3.5 text-cyan-400" />
                    {selectedRepo.branch.toUpperCase()}
                  </span>
                </div>
              </div>

              {detailsLoading ? (
                <div className="flex-1 flex items-center justify-center py-20 text-xs font-mono text-slate-500">
                  Fetching repository statistics...
                </div>
              ) : details ? (
                <div className="flex flex-col gap-5 flex-1 my-2 overflow-y-auto max-h-[480px] pr-1">
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Left Column: Commits Feed */}
                    <div className="space-y-3.5">
                      <h3 className="text-[10px] font-mono uppercase tracking-widest flex items-center gap-2 text-slate-400">
                        <GitCommit className="w-3.5 h-3.5 text-cyan-500" /> Commits Activity
                      </h3>

                      <div className={`p-4 rounded-xl border space-y-3 flex-1 overflow-y-auto max-h-[300px] ${
                        isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                      }`}>
                        {details.commits.length === 0 ? (
                          <p className="text-[10px] text-slate-500 font-mono">No recent commits found.</p>
                        ) : (
                          details.commits.map((c) => (
                            <div key={c.sha} className="flex flex-col gap-1 border-b border-slate-800/10 pb-2.5 last:border-0 last:pb-0">
                              <div className="flex items-center justify-between">
                                <span className="text-[9px] font-mono text-cyan-400 bg-cyan-950/20 border border-cyan-800/30 px-1.5 py-0.5 rounded uppercase">{c.sha}</span>
                                <span className="text-[9px] font-mono text-slate-500">{new Date(c.date).toLocaleDateString()}</span>
                              </div>
                              <p className="text-xs text-slate-300 font-medium line-clamp-1">{c.message}</p>
                              <span className="text-[9px] text-slate-500 font-mono">By: {c.author}</span>
                            </div>
                          ))
                        )}
                      </div>
                    </div>

                    {/* Right Column: Open Tickets & PR Stats */}
                    <div className="space-y-4">
                      <h3 className="text-[10px] font-mono uppercase tracking-widest flex items-center gap-2 text-slate-400">
                        <GitPullRequest className="w-3.5 h-3.5 text-indigo-500" /> Open Tickets
                      </h3>

                      <div className="grid grid-cols-2 gap-3">
                        <div className={`p-4 border rounded-xl flex flex-col justify-between gap-1 ${
                          isLight ? 'bg-white border-slate-200 shadow-sm' : 'bg-slate-900/40 border-slate-900'
                        }`}>
                          <span className="text-[9px] font-mono text-slate-500 uppercase">Open Issues</span>
                          <span className="text-xl font-bold font-display text-cyan-400">{details.open_issues_count}</span>
                        </div>
                        <div className={`p-4 border rounded-xl flex flex-col justify-between gap-1 ${
                          isLight ? 'bg-white border-slate-200 shadow-sm' : 'bg-slate-900/40 border-slate-900'
                        }`}>
                          <span className="text-[9px] font-mono text-slate-500 uppercase">Pull Requests</span>
                          <span className="text-xl font-bold font-display text-purple-400">{details.open_prs_count}</span>
                        </div>
                      </div>

                      <div className={`p-4 rounded-xl border flex-1 overflow-y-auto max-h-[190px] ${
                        isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                      }`}>
                        <span className="text-[10px] font-mono text-slate-500 uppercase block mb-2">Recent Open Issues</span>
                        {details.recent_issues.length === 0 ? (
                          <p className="text-[10px] text-slate-500 font-mono">No active open issues.</p>
                        ) : (
                          <div className="space-y-2">
                            {details.recent_issues.map((issue) => (
                              <div key={issue.number} className="text-xs flex flex-col gap-0.5 border-b border-slate-800/10 pb-2 last:border-0 last:pb-0">
                                <div className="flex items-center gap-1 text-[10px] text-slate-400">
                                  <span className="text-indigo-400 font-bold">#{issue.number}</span>
                                  <span className="truncate">{issue.user}</span>
                                </div>
                                <p className="text-xs text-slate-300 font-medium truncate">{issue.title}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Extended Details Section */}
                  <div className="border-t border-slate-200/10 pt-4 mt-2">
                    {!showExtended ? (
                      <button
                        onClick={fetchExtendedRepoDetails}
                        disabled={extendedLoading}
                        className="w-full py-3 bg-cyan-600/15 hover:bg-cyan-600/25 border border-cyan-500/20 text-cyan-400 rounded-xl text-xs font-bold font-mono tracking-wider transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50"
                      >
                        <RefreshCw className={`w-4 h-4 ${extendedLoading ? "animate-spin" : ""}`} />
                        {extendedLoading ? "FETCHING EXTENDED ANALYTICS..." : "FETCH EXTENDED ANALYTICS (CONTRIBUTORS, RELEASES, ACTIONS)"}
                      </button>
                    ) : extendedDetails ? (
                      <div className="space-y-5">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-bold font-display text-cyan-400">Extended Repository Analytics</h3>
                          <button
                            onClick={() => setShowExtended(false)}
                            className="text-[10px] font-mono text-slate-500 hover:text-slate-350 cursor-pointer underline"
                          >
                            Hide Extended Details
                          </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                          {/* Contributors Card */}
                          <div className={`p-4 rounded-xl border flex flex-col gap-3 ${
                            isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                          }`}>
                            <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Contributors</h4>
                            <div className="space-y-2 overflow-y-auto max-h-[140px] pr-1">
                              {extendedDetails.contributors.length === 0 ? (
                                <p className="text-[10px] text-slate-500 font-mono">No contributors found.</p>
                              ) : (
                                extendedDetails.contributors.map((c) => (
                                  <div key={c.login} className="flex items-center justify-between text-xs">
                                    <div className="flex items-center gap-2">
                                      <img src={c.avatar_url} alt={c.login} className="w-5 h-5 rounded-full border border-slate-700 object-cover" />
                                      <span className="font-medium text-slate-300 truncate max-w-[90px]">{c.login}</span>
                                    </div>
                                    <span className="font-mono text-[10px] text-cyan-400 bg-cyan-950/20 border border-cyan-900/20 px-1.5 py-0.2 rounded-full">
                                      {c.contributions}
                                    </span>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>

                          {/* Releases Card */}
                          <div className={`p-4 rounded-xl border flex flex-col gap-3 ${
                            isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                          }`}>
                            <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Latest Releases</h4>
                            <div className="space-y-2 overflow-y-auto max-h-[140px] pr-1">
                              {extendedDetails.releases.length === 0 ? (
                                <p className="text-[10px] text-slate-500 font-mono">No active releases found.</p>
                              ) : (
                                extendedDetails.releases.map((r) => (
                                  <div key={r.tag_name} className="flex flex-col gap-0.5 text-xs">
                                    <div className="flex items-center justify-between">
                                      <a href={r.html_url} target="_blank" rel="noopener noreferrer" className="text-cyan-400 font-bold hover:underline truncate max-w-[110px]">
                                        {r.tag_name}
                                      </a>
                                      <span className="text-[9px] font-mono text-slate-500">{new Date(r.published_at).toLocaleDateString()}</span>
                                    </div>
                                    <p className="text-[10px] text-slate-450 truncate">{r.name}</p>
                                  </div>
                                ))
                              )}
                            </div>
                          </div>

                          {/* Workflow/Action Runs Card */}
                          <div className={`p-4 rounded-xl border flex flex-col gap-3 ${
                            isLight ? 'bg-slate-50/50 border-slate-200' : 'bg-slate-900/20 border-slate-900/60'
                          }`}>
                            <h4 className="text-[10px] font-mono uppercase tracking-wider text-slate-400">Workflow Runs</h4>
                            <div className="space-y-2 overflow-y-auto max-h-[140px] pr-1">
                              {extendedDetails.workflow_runs.length === 0 ? (
                                <p className="text-[10px] text-slate-500 font-mono">No workflow runs found.</p>
                              ) : (
                                extendedDetails.workflow_runs.map((w) => {
                                  const isSuccess = w.conclusion === "success";
                                  const isFailure = w.conclusion === "failure";
                                  return (
                                    <div key={w.id} className="flex items-start justify-between gap-1 text-[11px] border-b border-slate-800/10 pb-1.5 last:border-0 last:pb-0">
                                      <div className="flex flex-col gap-0.5 max-w-[120px]">
                                        <span className="font-bold text-slate-350 truncate">{w.name}</span>
                                        <span className="text-[9px] font-mono text-slate-550 truncate">{w.commit_message || "No commit msg"}</span>
                                      </div>
                                      <span className={`text-[8px] font-mono px-1.5 py-0.5 rounded uppercase tracking-wider ${
                                        isSuccess ? "bg-emerald-950/30 text-emerald-450 border border-emerald-900/30" : 
                                        isFailure ? "bg-rose-950/30 text-rose-450 border border-rose-900/30" :
                                        "bg-amber-950/30 text-amber-450 border border-amber-900/30"
                                      }`}>
                                        {w.conclusion || w.status}
                                      </span>
                                    </div>
                                  );
                                })
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ) : null}
                  </div>

                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center text-xs font-mono text-slate-500">
                  Failed to load repository details.
                </div>
              )}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center flex-1 text-center py-20">
              <BookOpen className="w-12 h-12 mb-2 text-slate-700" />
              <p className="text-sm text-slate-500">Select a repository from the left panel to analyze activity.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
