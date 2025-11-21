from typing import List, Dict, Optional
from app.models import FilePatch, Hunk, LineChange
import re
from app.utils.logger import setup_logger

logger = setup_logger()

class DiffParser:
    """
    Parse unified diff format from GitHub PRs
    """
    
    @staticmethod
    def parse_unified_diff(diff_text: str) -> List[FilePatch]:
        """Parse unified diff format into FilePatch objects."""
        files = []
        lines = diff_text.split('\n')
        
        current_file = None
        current_hunks = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # File header
            if line.startswith('diff --git'):
                # Save previous file
                if current_file:
                    current_file['hunks'] = current_hunks
                    files.append(current_file)
                
                # Parse new file
                match = re.search(r'a/(.+?)\s+b/(.+?)$', line)
                if match:
                    filename = match.group(2)
                    current_file = {
                        'filename': filename,
                        'status': 'modified',
                        'additions': 0,
                        'deletions': 0,
                        'hunks': []
                    }
                    current_hunks = []
            
            # File status
            elif line.startswith('new file'):
                if current_file:
                    current_file['status'] = 'added'
            elif line.startswith('deleted file'):
                if current_file:
                    current_file['status'] = 'removed'
            
            # Hunk header
            elif line.startswith('@@'):
                match = re.search(r'@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@', line)
                if match:
                    old_start = int(match.group(1))
                    old_count = int(match.group(2)) if match.group(2) else 1
                    new_start = int(match.group(3))
                    new_count = int(match.group(4)) if match.group(4) else 1
                    
                    hunk = {
                        'old_start': old_start,
                        'old_count': old_count,
                        'new_start': new_start,
                        'new_count': new_count,
                        'lines': []
                    }
                    
                    # Parse hunk lines
                    i += 1
                    while i < len(lines) and not lines[i].startswith('@@') and not lines[i].startswith('diff'):
                        hunk_line = lines[i]
                        
                        if hunk_line.startswith('+') and not hunk_line.startswith('+++'):
                            hunk['lines'].append({
                                'content': hunk_line[1:],
                                'change_type': 'add',
                                'line_number': new_start
                            })
                            new_start += 1
                            if current_file:
                                current_file['additions'] += 1
                        elif hunk_line.startswith('-') and not hunk_line.startswith('---'):
                            hunk['lines'].append({
                                'content': hunk_line[1:],
                                'change_type': 'remove',
                                'line_number': old_start
                            })
                            old_start += 1
                            if current_file:
                                current_file['deletions'] += 1
                        elif hunk_line.startswith(' '):
                            hunk['lines'].append({
                                'content': hunk_line[1:],
                                'change_type': 'context',
                                'line_number': new_start
                            })
                            old_start += 1
                            new_start += 1
                        
                        i += 1
                    
                    current_hunks.append(hunk)
                    i -= 1
            
            i += 1
        
        # Don't forget the last file
        if current_file:
            current_file['hunks'] = current_hunks
            files.append(current_file)
        
        logger.info(f"Parsed diff: {len(files)} files changed")
        
        for f in files:
            logger.debug(f"  {f['filename']}: +{f['additions']} -{f['deletions']} lines")
        
        return [FilePatch(**f) for f in files]