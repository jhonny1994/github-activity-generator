"""
Tests for contribute.py (enhanced fast-import version).
"""
import os
import shutil
import tempfile
import unittest
from subprocess import check_output

import contribute


class TestContribute(unittest.TestCase):
    """Test cases for the contribution generator."""

    def test_parse_args_defaults(self):
        """Test default argument values."""
        config = contribute.parse_args([])
        self.assertFalse(config.no_weekends)
        self.assertEqual(config.max_commits, 10)
        self.assertEqual(config.frequency, 80)
        self.assertEqual(config.days_before, 365)
        self.assertEqual(config.days_after, 0)
        self.assertIsNone(config.repository)
        self.assertFalse(config.force)
        self.assertFalse(config.append)

    def test_parse_args_no_weekends(self):
        """Test --no_weekends flag."""
        config = contribute.parse_args(['-nw'])
        self.assertTrue(config.no_weekends)

    def test_parse_args_all_options(self):
        """Test all CLI options."""
        config = contribute.parse_args([
            '-nw',
            '-mc=5',
            '-fr=50',
            '-db=30',
            '-da=10',
            '-un=TestUser',
            '-ue=test@example.com',
            '-r=https://github.com/test/repo.git',
            '--force',
        ])
        self.assertTrue(config.no_weekends)
        self.assertEqual(config.max_commits, 5)
        self.assertEqual(config.frequency, 50)
        self.assertEqual(config.days_before, 30)
        self.assertEqual(config.days_after, 10)
        self.assertEqual(config.user_name, 'TestUser')
        self.assertEqual(config.user_email, 'test@example.com')
        self.assertEqual(config.repository, 'https://github.com/test/repo.git')
        self.assertTrue(config.force)

    def test_validate_config_negative_days(self):
        """Test validation rejects negative days."""
        config = contribute.Config(
            no_weekends=False, max_commits=10, frequency=80,
            days_before=-1, days_after=0, repository=None,
            user_name=None, user_email=None, force=False, append=False,
        )
        with self.assertRaises(SystemExit):
            contribute.validate_config(config)

    def test_validate_config_invalid_frequency(self):
        """Test validation rejects invalid frequency."""
        config = contribute.Config(
            no_weekends=False, max_commits=10, frequency=150,
            days_before=30, days_after=0, repository=None,
            user_name=None, user_email=None, force=False, append=False,
        )
        with self.assertRaises(SystemExit):
            contribute.validate_config(config)

    def test_validate_config_append_requires_repo(self):
        """Test that --append requires --repository."""
        config = contribute.Config(
            no_weekends=False, max_commits=10, frequency=80,
            days_before=30, days_after=0, repository=None,
            user_name=None, user_email=None, force=False, append=True,
        )
        with self.assertRaises(SystemExit):
            contribute.validate_config(config)

    def test_commits_generation(self):
        """Test that commits are actually generated."""
        original_dir = os.getcwd()
        test_dir = tempfile.mkdtemp(prefix="contrib_test_")
        
        try:
            os.chdir(test_dir)
            contribute.main([
                '-nw',
                '--user_name=TestUser',
                '--user_email=test@users.noreply.github.com',
                '-mc=3',
                '-fr=100',
                '-db=7',
                '-da=0',
            ])
            
            # Find generated repo
            repos = [d for d in os.listdir(test_dir) 
                     if os.path.isdir(os.path.join(test_dir, d)) 
                     and d.startswith('repository-')]
            self.assertEqual(len(repos), 1, f"Expected 1 repo, found: {repos}")
            
            repo_path = os.path.join(test_dir, repos[0])
            os.chdir(repo_path)
            
            # Check commits exist
            commit_count = int(check_output(
                ['git', 'rev-list', '--count', 'HEAD']
            ).decode('utf-8').strip())
            
            # With 7 days, no weekends (5 weekdays), 100% freq, 1-3 commits/day
            self.assertGreaterEqual(commit_count, 1)
            self.assertLessEqual(commit_count, 21)
            
        finally:
            os.chdir(original_dir)
            shutil.rmtree(test_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
