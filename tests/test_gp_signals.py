#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_gp_signals
----------------------------------

Tests for GP signal modules.
"""


import unittest
import numpy as np

from tests.enterprise_test_data import datadir
from enterprise.pulsar import Pulsar
from enterprise.signals import parameter
from enterprise.signals import selections
from enterprise.signals.signal_base import Function
from enterprise.signals.selections import Selection
import enterprise.signals.gp_signals as gs
from enterprise.signals import utils


class TestGPSignals(unittest.TestCase):

    def setUp(self):
        """Setup the Pulsar object."""

        # initialize Pulsar class
        self.psr = Pulsar(datadir + '/B1855+09_NANOGrav_11yv0.gls.par',
                          datadir + '/B1855+09_NANOGrav_11yv0.tim')

    def test_ecorr(self):
        """Test that ecorr signal returns correct values."""
        # set up signal parameter
        ecorr = parameter.Uniform(-10, -5)
        ec = gs.EcorrBasisModel(log10_ecorr=ecorr)
        ecm = ec(self.psr)

        # parameters
        ecorr = -6.4
        params = {'B1855+09_log10_ecorr': ecorr}

        # basis matrix test
        U = utils.create_quantization_matrix(self.psr.toas)
        msg = 'U matrix incorrect for Basis Ecorr signal.'
        assert np.allclose(U, ecm.get_basis(params)), msg

        # Jvec test
        jvec = 10**(2*ecorr) * np.ones(U.shape[1])
        msg = 'Prior vector incorrect for Basis Ecorr signal.'
        assert np.all(ecm.get_phi(params) == jvec), msg

        # inverse Jvec test
        msg = 'Prior vector inverse incorrect for Basis Ecorr signal.'
        assert np.all(ecm.get_phiinv(params) == 1/jvec), msg

        # test shape
        msg = 'U matrix shape incorrect'
        assert ecm.basis_shape == U.shape, msg

    def test_ecorr_backend(self):
        """Test that ecorr-backend signal returns correct values."""
        # set up signal parameter
        ecorr = parameter.Uniform(-10, -5)
        selection = Selection(selections.by_backend)
        ec = gs.EcorrBasisModel(log10_ecorr=ecorr, selection=selection)
        ecm = ec(self.psr)

        # parameters
        ecorrs = [-6.1, -6.2, -6.3, -6.4]
        params = {'B1855+09_log10_ecorr_430_ASP': ecorrs[0],
                  'B1855+09_log10_ecorr_430_PUPPI': ecorrs[1],
                  'B1855+09_log10_ecorr_L-wide_ASP': ecorrs[2],
                  'B1855+09_log10_ecorr_L-wide_PUPPI': ecorrs[3]}

        # get the basis
        bflags = self.psr.backend_flags
        Umats = []
        for flag in np.unique(bflags):
            mask = bflags == flag
            Umats.append(utils.create_quantization_matrix(self.psr.toas[mask]))
        nepoch = sum(U.shape[1] for U in Umats)
        U = np.zeros((len(self.psr.toas), nepoch))
        jvec = np.zeros(nepoch)
        netot = 0
        for ct, flag in enumerate(np.unique(bflags)):
            mask = bflags == flag
            nn = Umats[ct].shape[1]
            U[mask, netot:nn+netot] = Umats[ct]
            jvec[netot:nn+netot] = 10**(2*ecorrs[ct])
            netot += nn

        # basis matrix test
        msg = 'U matrix incorrect for Basis Ecorr-backend signal.'
        assert np.allclose(U, ecm.get_basis(params)), msg

        # Jvec test
        msg = 'Prior vector incorrect for Basis Ecorr backend signal.'
        assert np.all(ecm.get_phi(params) == jvec), msg

        # inverse Jvec test
        msg = 'Prior vector inverse incorrect for Basis Ecorr backend signal.'
        assert np.all(ecm.get_phiinv(params) == 1/jvec), msg

        # test shape
        msg = 'U matrix shape incorrect'
        assert ecm.basis_shape == U.shape, msg

    def test_fourier_red_noise(self):
        """Test that red noise signal returns correct values."""
        # set up signal parameter
        pl = Function(utils.powerlaw, log10_A=parameter.Uniform(-18,-12),
                      gamma=parameter.Uniform(1,7))
        rn = gs.FourierBasisGP(spectrum=pl, components=30)
        rnm = rn(self.psr)

        # parameters
        log10_A, gamma = -14.5, 4.33
        params = {'B1855+09_log10_A': log10_A,
                  'B1855+09_gamma': gamma}

        # basis matrix test
        F, f2, _ = utils.createfourierdesignmatrix_red(
            self.psr.toas, nmodes=30, freq=True)
        msg = 'F matrix incorrect for GP Fourier signal.'
        assert np.allclose(F, rnm.get_basis(params)), msg

        # spectrum test
        phi = utils.powerlaw(f2, log10_A=log10_A, gamma=gamma) * f2[0]
        msg = 'Spectrum incorrect for GP Fourier signal.'
        assert np.all(rnm.get_phi(params) == phi), msg

        # inverse spectrum test
        msg = 'Spectrum inverse incorrect for GP Fourier signal.'
        assert np.all(rnm.get_phiinv(params) == 1/phi), msg

        # test shape
        msg = 'F matrix shape incorrect'
        assert rnm.basis_shape == F.shape, msg

    def test_fourier_red_noise_backend(self):
        """Test that red noise-backend signal returns correct values."""
        # set up signal parameter
        pl = Function(utils.powerlaw, log10_A=parameter.Uniform(-18,-12),
                      gamma=parameter.Uniform(1,7))
        selection = Selection(selections.by_backend)
        rn = gs.FourierBasisGP(spectrum=pl, components=30, selection=selection)
        rnm = rn(self.psr)

        # parameters
        log10_As = [-14, -14.4, -15, -14.8]
        gammas = [2.3, 4.4, 1.8, 5.6]
        params = {'B1855+09_gamma_430_ASP': gammas[0],
                  'B1855+09_gamma_430_PUPPI': gammas[1],
                  'B1855+09_gamma_L-wide_ASP': gammas[2],
                  'B1855+09_gamma_L-wide_PUPPI': gammas[3],
                  'B1855+09_log10_A_430_ASP': log10_As[0],
                  'B1855+09_log10_A_430_PUPPI': log10_As[1],
                  'B1855+09_log10_A_L-wide_ASP': log10_As[2],
                  'B1855+09_log10_A_L-wide_PUPPI': log10_As[3]}

        # get the basis
        bflags = self.psr.backend_flags
        Fmats, fs, phis = [], [], []
        for ct, flag in enumerate(np.unique(bflags)):
            mask = bflags == flag
            F, f, _ = utils.createfourierdesignmatrix_red(
                self.psr.toas[mask], 30, freq=True)
            Fmats.append(F)
            fs.append(f)
            phis.append(utils.powerlaw(f, log10_As[ct], gammas[ct])*f[0])

        nf = sum(F.shape[1] for F in Fmats)
        F = np.zeros((len(self.psr.toas), nf))
        phi = np.hstack(p for p in phis)
        nftot = 0
        for ct, flag in enumerate(np.unique(bflags)):
            mask = bflags == flag
            nn = Fmats[ct].shape[1]
            F[mask, nftot:nn+nftot] = Fmats[ct]
            nftot += nn

        msg = 'F matrix incorrect for GP Fourier backend signal.'
        assert np.allclose(F, rnm.get_basis(params)), msg

        # spectrum test
        msg = 'Spectrum incorrect for GP Fourier backend signal.'
        assert np.all(rnm.get_phi(params) == phi), msg

        # inverse spectrum test
        msg = 'Spectrum inverse incorrect for GP Fourier backend signal.'
        assert np.all(rnm.get_phiinv(params) == 1/phi), msg

        # test shape
        msg = 'F matrix shape incorrect'
        assert rnm.basis_shape == F.shape, msg

    def test_red_noise_add(self):
        """Test that red noise addition only returns independent columns."""
        # set up signals
        pl = Function(utils.powerlaw, log10_A=parameter.Uniform(-18,-12),
                      gamma=parameter.Uniform(1,7))
        cpl = Function(utils.powerlaw,
                       log10_A=parameter.Uniform(-18,-12)('log10_Agw'),
                       gamma=parameter.Uniform(1,7)('gamma_gw'))

        # parameters
        log10_A, gamma = -14.5, 4.33
        log10_Ac, gammac = -15.5, 1.33
        params = {'B1855+09_log10_A': log10_A,
                  'B1855+09_gamma': gamma,
                  'log10_Agw': log10_Ac,
                  'gamma_gw': gammac}

        Tmax = self.psr.toas.max() - self.psr.toas.min()
        tpars = [(30, 20, Tmax, Tmax), (20, 30, Tmax, Tmax),
                 (30, 30, Tmax, Tmax), (30, 20, Tmax, 1.123*Tmax),
                 (20, 30, Tmax, 1.123*Tmax), (30, 30, 1.123*Tmax, Tmax)]

        for (nf1, nf2, T1, T2) in tpars:

            rn = gs.FourierBasisGP(spectrum=pl, components=nf1, Tspan=T1)
            crn = gs.FourierBasisGP(spectrum=cpl, components=nf2, Tspan=T2)
            s = rn + crn
            rnm = s(self.psr)

            # set up frequencies
            F1, f1, _ = utils.createfourierdesignmatrix_red(
                self.psr.toas, nmodes=nf1, freq=True, Tspan=T1)
            F2, f2, _ = utils.createfourierdesignmatrix_red(
                self.psr.toas, nmodes=nf2, freq=True, Tspan=T2)

            # test power spectrum
            p1 = utils.powerlaw(f1, log10_A, gamma) * f1[0]
            p2 = utils.powerlaw(f2, log10_Ac, gammac) * f2[0]
            if T1 == T2:
                nf = max(2*nf1, 2*nf2)
                phi = np.zeros(nf)
                F = F1 if nf1 > nf2 else F2
                phi[:2*nf1] = p1
                phi[:2*nf2] += p2
                F[:,]
            else:
                phi = np.concatenate((p1, p2))
                F = np.hstack((F1, F2))

            msg = 'Combined red noise PSD incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.all(rnm.get_phi(params) == phi), msg

            msg = 'Combined red noise PSD inverse incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.all(rnm.get_phiinv(params) == 1/phi), msg

            msg = 'Combined red noise Fmat incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.allclose(F, rnm.get_basis(params)), msg

    def test_red_noise_add_backend(self):
        """Test that red noise with backend addition only returns
        independent columns."""
        # set up signals
        pl = Function(utils.powerlaw, log10_A=parameter.Uniform(-18,-12),
                      gamma=parameter.Uniform(1,7))
        selection = Selection(selections.by_backend)
        cpl = Function(utils.powerlaw,
                       log10_A=parameter.Uniform(-18,-12)('log10_Agw'),
                       gamma=parameter.Uniform(1,7)('gamma_gw'))

        # parameters
        log10_As = [-14, -14.4, -15, -14.8]
        gammas = [2.3, 4.4, 1.8, 5.6]
        log10_Ac, gammac = -15.5, 1.33
        params = {'B1855+09_gamma_430_ASP': gammas[0],
                  'B1855+09_gamma_430_PUPPI': gammas[1],
                  'B1855+09_gamma_L-wide_ASP': gammas[2],
                  'B1855+09_gamma_L-wide_PUPPI': gammas[3],
                  'B1855+09_log10_A_430_ASP': log10_As[0],
                  'B1855+09_log10_A_430_PUPPI': log10_As[1],
                  'B1855+09_log10_A_L-wide_ASP': log10_As[2],
                  'B1855+09_log10_A_L-wide_PUPPI': log10_As[3],
                  'log10_Agw': log10_Ac,
                  'gamma_gw': gammac}

        Tmax = self.psr.toas.max() - self.psr.toas.min()
        tpars = [(30, 20, Tmax, Tmax), (20, 30, Tmax, Tmax),
                 (30, 30, Tmax, Tmax), (30, 20, Tmax, 1.123*Tmax),
                 (20, 30, Tmax, 1.123*Tmax), (30, 30, 1.123*Tmax, Tmax),
                 (30, 20, None, Tmax)]

        for (nf1, nf2, T1, T2) in tpars:

            rn = gs.FourierBasisGP(spectrum=pl, components=nf1, Tspan=T1,
                                   selection=selection)
            crn = gs.FourierBasisGP(spectrum=cpl, components=nf2, Tspan=T2)
            s = rn + crn
            rnm = s(self.psr)

            # get the basis
            bflags = self.psr.backend_flags
            Fmats, fs, phis = [], [], []
            F2, f2, _ = utils.createfourierdesignmatrix_red(
                self.psr.toas, nf2, freq=True, Tspan=T2)
            p2 = utils.powerlaw(f2, log10_Ac, gammac)*f2[0]
            for ct, flag in enumerate(np.unique(bflags)):
                mask = bflags == flag
                F1, f1, _ = utils.createfourierdesignmatrix_red(
                    self.psr.toas[mask], nf1, freq=True, Tspan=T1)
                Fmats.append(F1)
                fs.append(f1)
                phis.append(utils.powerlaw(f1, log10_As[ct], gammas[ct])*f1[0])

            Fmats.append(F2)
            phis.append(p2)
            nf = sum(F.shape[1] for F in Fmats)
            F = np.zeros((len(self.psr.toas), nf))
            phi = np.hstack(p for p in phis)
            nftot = 0
            for ct, flag in enumerate(np.unique(bflags)):
                mask = bflags == flag
                nn = Fmats[ct].shape[1]
                F[mask, nftot:nn+nftot] = Fmats[ct]
                nftot += nn
            F[:, -2*nf2:] = F2

            msg = 'Combined red noise PSD incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.all(rnm.get_phi(params) == phi), msg

            msg = 'Combined red noise PSD inverse incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.all(rnm.get_phiinv(params) == 1/phi), msg

            msg = 'Combined red noise Fmat incorrect '
            msg += 'for {} {} {} {}'.format(nf1, nf2, T1, T2)
            assert np.allclose(F, rnm.get_basis(params)), msg

    def test_gp_timing_model(self):
        """Test that the timing model signal returns correct values."""
        # set up signal parameter
        ts = gs.TimingModel()
        tm = ts(self.psr)

        # basis matrix test
        M = self.psr.Mmat.copy()
        norm = np.sqrt(np.sum(M**2, axis=0))
        M /= norm
        msg = 'M matrix incorrect for Timing Model signal.'
        assert np.allclose(M, tm.get_basis()), msg

        # Jvec test
        phi = np.ones(self.psr.Mmat.shape[1]) * 1e40
        msg = 'Prior vector incorrect for Timing Model signal.'
        assert np.all(tm.get_phi() == phi), msg

        # inverse Jvec test
        msg = 'Prior vector inverse incorrect for Timing Model signal.'
        assert np.all(tm.get_phiinv() == 1/phi), msg

        # test shape
        msg = 'M matrix shape incorrect'
        assert tm.basis_shape == self.psr.Mmat.shape, msg

    def test_combine_signals(self):
        """Test for combining different signals."""
        # set up signal parameter
        ecorr = parameter.Uniform(-10, -5)
        ec = gs.EcorrBasisModel(log10_ecorr=ecorr)

        pl = Function(utils.powerlaw, log10_A=parameter.Uniform(-18,-12),
                      gamma=parameter.Uniform(1,7))
        rn = gs.FourierBasisGP(spectrum=pl, components=30)
        ts = gs.TimingModel()
        s = ec + rn + ts
        m = s(self.psr)

        # parameters
        ecorr = -6.4
        log10_A, gamma = -14.5, 4.33
        params = {'B1855+09_log10_ecorr': ecorr,
                  'B1855+09_log10_A': log10_A,
                  'B1855+09_gamma': gamma}

        # combined basis matrix
        U = utils.create_quantization_matrix(self.psr.toas)
        M = self.psr.Mmat.copy()
        norm = np.sqrt(np.sum(M**2, axis=0))
        M /= norm
        F, f2, _ = utils.createfourierdesignmatrix_red(
            self.psr.toas, nmodes=30, freq=True)
        T = np.hstack((U, F, M))

        # combined prior vector
        jvec = 10**(2*ecorr) * np.ones(U.shape[1])
        phim = np.ones(self.psr.Mmat.shape[1]) * 1e40
        phi = utils.powerlaw(f2, log10_A=log10_A, gamma=gamma) * f2[0]
        phivec = np.concatenate((jvec, phi, phim))

        # basis matrix test
        msg = 'Basis matrix incorrect for combined signal.'
        assert np.allclose(T, m.get_basis(params)), msg

        # Jvec test
        msg = 'Prior vector incorrect for combined signal.'
        assert np.all(m.get_phi(params) == phivec), msg

        # inverse Jvec test
        msg = 'Prior vector inverse incorrect for combined signal.'
        assert np.all(m.get_phiinv(params) == 1/phivec), msg

        # test shape
        msg = 'Basis matrix shape incorrect size for combined signal.'
        assert m.basis_shape == T.shape, msg
