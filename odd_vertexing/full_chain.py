#!/usr/bin/env python3
import argparse
import pathlib, acts, acts.examples
import acts.examples.dd4hep
from common import getOpenDataDetector, getOpenDataDetectorDirectory


u = acts.UnitConstants
outputDir = pathlib.Path.cwd() / "odd_output"
outputDir.mkdir(exist_ok=True)

oddDir = getOpenDataDetectorDirectory()

oddMaterialMap = oddDir / "data/odd-material-maps.root"
oddDigiConfig = oddDir / "config/odd-digi-smearing-config.json"
oddSeedingSel = oddDir / "config/odd-seeding-config.json"
oddMaterialDeco = acts.IMaterialDecorator.fromFile(oddMaterialMap)

detector, trackingGeometry, decorators = getOpenDataDetector(mdecorator=oddMaterialDeco)
field = acts.ConstantBField(acts.Vector3(0.0, 0.0, 2.0 * u.T))
rnd = acts.examples.RandomNumbers(seed=42)

from particle_gun import addParticleGun, MomentumConfig, EtaConfig, ParticleConfig
from fatras import addFatras
from digitization import addDigitization
from seeding import addSeeding, SeedfinderConfigArg, TruthSeedRanges
from ckf_tracks import addCKFTracks, CKFPerformanceConfig
from vertex_fitting import addVertexFitting, VertexFinder

s = acts.examples.Sequencer(skip=20, events=1, numThreads=1, logLevel=acts.logging.INFO)

s = addParticleGun(
    s,
    MomentumConfig(1.0 * u.GeV, 10.0 * u.GeV, True),
    EtaConfig(-3.0, 3.0, True),
    ParticleConfig(2, acts.PdgParticle.eMuon, True),
    rnd=rnd,
)
s = addFatras(
    s,
    trackingGeometry,
    field,
    outputDirRoot=outputDir,
    rnd=rnd,
)
s = addDigitization(
    s,
    trackingGeometry,
    field,
    digiConfigFile=oddDigiConfig,
    outputDirRoot=outputDir,
    rnd=rnd,
)
s = addSeeding(
    s,
    trackingGeometry,
    field,
    SeedfinderConfigArg(
        r=(33 * u.mm, 300 * u.mm),
        collisionRegion=(-250 * u.mm, 250 * u.mm),
        z=(-2000 * u.mm, 2000 * u.mm),
        maxSeedsPerSpM=0,
        bFieldInZ=2 * u.T,
        impactMax=3 * u.mm,
        cotThetaMax=17,
    ),
    geoSelectionConfigFile=oddSeedingSel,
    outputDirRoot=outputDir,
)
s = addCKFTracks(
    s,
    trackingGeometry,
    field,
    CKFPerformanceConfig(ptMin=400.0 * u.MeV, nMeasurementsMin=6),
    outputDirRoot=outputDir,
)
s.addAlgorithm(
    acts.examples.TrackSelector(
        level=acts.logging.INFO,
        inputTrackParameters="fittedTrackParameters",
        outputTrackParameters="trackparameters",
        outputTrackIndices="outputTrackIndices",
    )
)
s = addVertexFitting(
    s,
    field,
    vertexFinder=VertexFinder.AMVF,
    outputDirRoot=outputDir,
    logLevel=acts.logging.VERBOSE,
)

s.run()
